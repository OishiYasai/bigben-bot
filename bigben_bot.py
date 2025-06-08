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

# Set timezone to Luxembourg
LUX_TIMEZONE = pytz.timezone("Europe/Luxembourg")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# Discord intents
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True  # Needed to count non-bot members in channels

# Scheduler setup
scheduler = AsyncIOScheduler(timezone=LUX_TIMEZONE)

# Core function to join a voice channel and play gongs
async def play_hourly_gongs():
    logging.info("Looking for voice channel to join...")

    for guild in client.guilds:
        most_populated_channel = None
        max_users = 0

        for channel in guild.voice_channels:
            user_count = len([m for m in channel.members if not m.bot])
            logging.info(f"Channel '{channel.name}' has {user_count} non-bot users")
            if user_count > max_users:
                max_users = user_count
                most_populated_channel = channel

        if most_populated_channel and max_users > 0:
            logging.info(f"Joining channel: {most_populated_channel.name} with {max_users} users")
            try:
                vc = await most_populated_channel.connect()
                now = datetime.now(LUX_TIMEZONE)
                hour = now.hour if now.hour <= 12 else now.hour - 12
                hour = 12 if hour == 0 else hour

                logging.info(f"Playing {hour} gong(s) for hour {now.hour}")

                for i in range(hour):
                    logging.info(f"Playing gong #{i + 1}")
                    vc.play(discord.FFmpegPCMAudio(GONG_SOUND_PATH))
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    await asyncio.sleep(1)

                await vc.disconnect()
                logging.info("Disconnected from voice channel.")

            except Exception as e:
                logging.error(f"Failed to join or play audio: {e}")
        else:
            logging.warning("No populated voice channels found.")

# Custom bot client
class BigBenBot(discord.Client):
    async def setup_hook(self):
        logging.info("setup_hook: Running test gong playback on startup...")
        await play_hourly_gongs()

# Create bot instance
client = BigBenBot(intents=intents)

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user}")
    scheduler.add_job(play_hourly_gongs, CronTrigger(minute=0))
    scheduler.start()
    logging.info("Scheduler started for hourly gongs.")

# Run the bot
client.run(TOKEN)
