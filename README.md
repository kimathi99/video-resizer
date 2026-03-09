# Video Compressor

Compress `.mov` and `.mp4` videos to a target maximum file size using `ffmpeg`, and save results as `.mp4`.

## What this does

- Reads input videos from a folder (default: `videos/`)
- Compresses each video using 2-pass H.264 encoding
- Writes compressed files to an output folder (default: `output/`)
- Names outputs as `<original_name>_compressed.mp4`

## Requirements

- Python 3.10+ (3.11 recommended)
- `ffmpeg` and `ffprobe` installed and available in PATH

Quick check:

```bash
python3 --version
ffmpeg -version
ffprobe -version
```

## Project structure

```text
videocompressor/
  compress_video.py
  Dockerfile
  videos/      # input videos (ignored by git)
  output/      # compressed videos (ignored by git)
```

## Run locally

1. Put your source videos inside `videos/`
2. Run:

```bash
python3 compress_video.py --input-dir videos --output-dir output --max-size-mb 20
```

### Useful options

- `--input-dir`: folder containing input `.mov` / `.mp4` files
- `--output-dir`: folder where compressed `.mp4` files will be written
- `--max-size-mb`: maximum size per output video (in MB)

Example with custom size:

```bash
python3 compress_video.py --input-dir videos --output-dir output --max-size-mb 15
```

## Run with Docker

Build image:

```bash
docker build -t video-compressor .
```

Run container with local folders mounted:

```bash
docker run --rm \
  -v "$(pwd)/videos:/app/videos" \
  -v "$(pwd)/output:/app/output" \
  video-compressor
```

To override target size in Docker:

```bash
docker run --rm \
  -v "$(pwd)/videos:/app/videos" \
  -v "$(pwd)/output:/app/output" \
  video-compressor \
  python compress_video.py --input-dir /app/videos --output-dir /app/output --max-size-mb 15
```

## Notes

- Only `.mov` and `.mp4` input files are processed.
- Large/long videos may still end slightly above the target depending on content complexity.
- `videos/` and `output/` are intentionally excluded from git so media files are not pushed.
