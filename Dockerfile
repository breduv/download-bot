FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

COPY --from=denoland/deno:bin-2.6.9 /deno /usr/local/bin/deno

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -U bgutil-ytdlp-pot-provider

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]