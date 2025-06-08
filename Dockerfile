FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir discord.py apscheduler pytz

CMD ["python", "bigben_bot.py"]
