import discord
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GONG_SOUND_PATH = "gong.mp3"

# Timezone for Luxembourg
LUX_TIMEZONE = pytz.timezone("Europe/Luxembourg")

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# Discord intents
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

# Scheduler
scheduler = AsyncIOScheduler(timezone=LUX_TIMEZONE)

async def play_hourly_gongs():
    logging.info("Looking for voice channel to join...2")

    for guild in client.guilds:
        most_populated = None
        max_users = 0

        for channel in guild.voice_channels:
            logging.info(f"Checking channel: {channel.name}")
            for m in channel.members:
                logging.info(f"  Found member: {m.name} (bot={m.bot})")

            user_count = len([m for m in channel.members if not m.bot])
            logging.info(f"Channel '{channel.name}' has {user_count} non-bot users")

            if user_count > max_users:
                max_users = user_count
                most_populated = channel

        if most_populated and max_users > 0:
            logging.info(f"Joining channel: {most_populated.name} with {max_users} users")
            try:
                vc = await most_populated.connect()
                now = datetime.now(LUX_TIMEZONE)
                hour = now.hour if now.hour <= 12 else now.hour - 12
                hour = 12 if hour == 0 else hour

                logging.info(f"Playing {hour} gong(s) for hour {now.hour}")

                for i in range(hour):
                    logging.info(f"Playing gong #{i+1}")
                    vc.play(discord.FFmpegPCMAudio(GONG_SOUND_PATH))
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    await asyncio.sleep(1)

                await vc.disconnect()
                logging.info("Disconnected from voice channel.")
            except Exception as e:
                logging.error(f"Failed to join or play audio: {e}")
        else:
            logging.warning("No populated voice channels found. Is anyone in a voice channel?")

# Create client
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user}")
    # schedule hourly job
    scheduler.add_job(play_hourly_gongs, CronTrigger(minute=0))
    scheduler.start()
    logging.info("Scheduler started for hourly gongs.")
    # test once now that bot is fully ready
    logging.info("Running initial gong test now that bot is ready...")
    await play_hourly_gongs()

client.run(TOKEN)
