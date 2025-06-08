import discord
import asyncio
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Path to gong sound (you need a .mp3 or .wav file)
GONG_SOUND_PATH = "gong.mp3"

# Timezone for Luxembourg
LUX_TIMEZONE = pytz.timezone("Europe/Luxembourg")

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)

scheduler = AsyncIOScheduler(timezone=LUX_TIMEZONE)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    scheduler.add_job(play_hourly_gongs, CronTrigger(minute=0))
    scheduler.start()

async def play_hourly_gongs():
    for guild in client.guilds:
        most_populated_channel = None
        max_users = 0

        for channel in guild.voice_channels:
            user_count = len([member for member in channel.members if not member.bot])
            if user_count > max_users:
                max_users = user_count
                most_populated_channel = channel

        if most_populated_channel and max_users > 0:
            try:
                vc = await most_populated_channel.connect()
                now = datetime.now(LUX_TIMEZONE)
                hour = now.hour if now.hour <= 12 else now.hour - 12
                hour = 12 if hour == 0 else hour  # Handle midnight and noon

                for _ in range(hour):
                    vc.play(discord.FFmpegPCMAudio(GONG_SOUND_PATH))
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    await asyncio.sleep(1)  # Small pause between gongs

                await vc.disconnect()
            except Exception as e:
                print(f"Error connecting or playing in {most_populated_channel.name}: {e}")

async def test_now():
    await play_hourly_gongs()

client.loop.create_task(test_now())

client.run(TOKEN)
