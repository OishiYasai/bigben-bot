import discord
import asyncio
import logging
import random
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Folder containing your sound files (.mp3, .wav)
SOUND_FOLDER = "sounds"

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
    logging.info("Looking for voice channel to join...")
    # Load available sounds
    try:
        sounds = [
            f for f in os.listdir(SOUND_FOLDER)
            if f.lower().endswith(('.mp3', '.wav'))
        ]
        if not sounds:
            logging.error(f"No sound files found in '{SOUND_FOLDER}'")
            return
    except Exception as e:
        logging.error(f"Error reading sound folder '{SOUND_FOLDER}': {e}")
        return

    # Choose one random sound for this invocation (hour)
    chosen_sound = random.choice(sounds)
    sound_path = os.path.join(SOUND_FOLDER, chosen_sound)
    logging.info(f"Selected sound for this hour: {chosen_sound}")

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

                logging.info(f"Playing {hour} times '{chosen_sound}' for hour {now.hour}")

                for i in range(hour):
                    logging.info(f"Playing instance #{i+1}")
                    vc.play(discord.FFmpegPCMAudio(sound_path))
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
    # schedule hourly job at the top of every hour
    scheduler.add_job(play_hourly_gongs, CronTrigger(minute=0))
    scheduler.start()
    logging.info("Scheduler started for hourly gongs.")
    # initial test
    logging.info("Running initial gong test now that bot is ready...")
    await play_hourly_gongs()

client.run(TOKEN)
