"""
Discord Bot with Slash Commands + Render Keep Alive Fix
"""

import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Load environment variables
load_dotenv()

# -------------------------
# KEEP ALIVE WEB SERVER
# -------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# Start web server first (important for Render)
keep_alive()

# -------------------------
# DISCORD BOT SETUP
# -------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# -------------------------
# EVENTS
# -------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} command(s) with Discord")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# -------------------------
# SLASH COMMANDS
# -------------------------
@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot latency: **{latency}ms**",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="hello", description="Get a friendly greeting")
async def hello(interaction: discord.Interaction):
    embed = discord.Embed(
        title="👋 Hello!",
        description=f"Hi {interaction.user.mention}! Nice to meet you.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="info", description="Get information about the bot")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ Bot Information",
        color=discord.Color.purple()
    )
    embed.add_field(name="Bot Name", value=str(bot.user), inline=False)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=False)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=False)
    embed.set_footer(
        text=f"Requested by {interaction.user}",
        icon_url=interaction.user.display_avatar.url
    )

    await interaction.response.send_message(embed=embed)

# -------------------------
# START BOT
# -------------------------
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    bot.run(token)
