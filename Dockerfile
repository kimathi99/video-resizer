FROM python:3.11-slim

# install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY compress_video.py .
RUN mkdir -p /app/videos /app/output

CMD ["python", "compress_video.py", "--input-dir", "/app/videos", "--output-dir", "/app/output", "--max-size-mb", "20"]