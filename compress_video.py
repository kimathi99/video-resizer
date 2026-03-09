import argparse
import subprocess
from pathlib import Path


def run_command(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def probe_duration_seconds(input_file):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_file),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    if duration <= 0:
        raise ValueError(f"Invalid video duration for {input_file}")
    return duration


def choose_audio_bitrate_kbps(duration_seconds):
    if duration_seconds > 600:
        return 64
    return 96


def ensure_output_name(input_path, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{input_path.stem}_compressed.mp4"


def clean_passlog(passlog_base):
    for suffix in ("-0.log", "-0.log.mbtree"):
        file_path = Path(f"{passlog_base}{suffix}")
        if file_path.exists():
            file_path.unlink()


def compress_to_target_size(input_file, output_file, max_size_mb):
    duration_seconds = probe_duration_seconds(input_file)
    target_size_bytes = int(max_size_mb * 1024 * 1024)

    audio_kbps = choose_audio_bitrate_kbps(duration_seconds)
    minimum_video_bps = 100_000

    raw_total_bps = int((target_size_bytes * 8) / duration_seconds)
    bitrate_factors = [0.97, 0.93, 0.88]

    for factor in bitrate_factors:
        total_bps = int(raw_total_bps * factor)
        audio_bps = audio_kbps * 1000

        if total_bps <= audio_bps + minimum_video_bps:
            audio_kbps = 48
            audio_bps = audio_kbps * 1000

        video_bps = total_bps - audio_bps
        if video_bps < minimum_video_bps:
            video_bps = minimum_video_bps

        video_kbps = max(100, video_bps // 1000)
        passlog_base = str(output_file.with_suffix(""))

        # Pass 1: analyze video stream.
        cmd_pass1 = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_file),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            f"{video_kbps}k",
            "-maxrate",
            f"{video_kbps}k",
            "-bufsize",
            f"{video_kbps * 2}k",
            "-pass",
            "1",
            "-passlogfile",
            passlog_base,
            "-an",
            "-f",
            "mp4",
            "/dev/null",
        ]
        run_command(cmd_pass1)

        # Pass 2: encode final video + audio in mp4.
        cmd_pass2 = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_file),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            f"{video_kbps}k",
            "-maxrate",
            f"{video_kbps}k",
            "-bufsize",
            f"{video_kbps * 2}k",
            "-pass",
            "2",
            "-passlogfile",
            passlog_base,
            "-c:a",
            "aac",
            "-b:a",
            f"{audio_kbps}k",
            "-movflags",
            "+faststart",
            str(output_file),
        ]
        run_command(cmd_pass2)
        clean_passlog(passlog_base)

        output_size_bytes = output_file.stat().st_size
        if output_size_bytes <= target_size_bytes:
            return output_size_bytes, target_size_bytes

    return output_file.stat().st_size, target_size_bytes


def collect_input_files(input_dir):
    supported_extensions = {".mp4", ".mov"}
    return sorted([f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in supported_extensions])


def main():
    parser = argparse.ArgumentParser(
        description="Compress MOV/MP4 videos to a target maximum size and save as MP4 in output folder."
    )
    parser.add_argument("--input-dir", default="videos", help="Folder containing input video files (.mov, .mp4).")
    parser.add_argument("--output-dir", default="output", help="Folder for compressed mp4 files.")
    parser.add_argument("--max-size-mb", type=float, default=20.0, help="Max output size per video in MB.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    input_files = collect_input_files(input_dir)
    if not input_files:
        print(f"No supported video files (.mov, .mp4) found in {input_dir}")
        return

    print(f"Found {len(input_files)} video file(s). Target: <= {args.max_size_mb}MB each (output: .mp4)")
    for input_file in input_files:
        output_file = ensure_output_name(input_file, output_dir)
        print(f"\nCompressing: {input_file.name}")
        try:
            output_size, target_size = compress_to_target_size(input_file, output_file, args.max_size_mb)
            output_mb = output_size / (1024 * 1024)
            target_mb = target_size / (1024 * 1024)
            status = "OK" if output_size <= target_size else "OVER TARGET"
            print(f"Saved: {output_file} ({output_mb:.2f}MB / {target_mb:.2f}MB) [{status}]")
        except Exception as exc:
            print(f"Failed to compress {input_file.name}: {exc}")


if __name__ == "__main__":
    main()