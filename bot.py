"""
Discord Bot with Slash Commands
Main entry point for the bot
"""

import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Intents configuration
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix="/", intents=intents)


# Events
@bot.event
async def on_ready():
    """Called when the bot successfully connects to Discord"""
    print(f"✅ Bot is online as {bot.user}")
    print(f"📋 Synced {len(bot.tree.get_commands())} command(s)")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} command(s) with Discord")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


# Slash Commands
@bot.tree.command(
    name="ping",
    description="Check the bot's latency"
)
async def ping(interaction: discord.Interaction):
    """Ping command to check bot latency"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot latency: **{latency}ms**",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="hello",
    description="Get a friendly greeting"
)
async def hello(interaction: discord.Interaction):
    """Hello command"""
    embed = discord.Embed(
        title="👋 Hello!",
        description=f"Hi {interaction.user.mention}! Nice to meet you.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="info",
    description="Get information about the bot"
)
async def info(interaction: discord.Interaction):
    """Bot info command"""
    embed = discord.Embed(
        title="ℹ️ Bot Information",
        color=discord.Color.purple()
    )
    embed.add_field(name="Bot Name", value=bot.user.name, inline=False)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=False)
    embed.add_field(name="Discord.py Version", value=discord.version_info.major, inline=False)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
    
    await interaction.response.send_message(embed=embed)


async def main():
    """Start the bot"""
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        raise ValueError(
            "❌ DISCORD_TOKEN not found in .env file!\n"
            "Please create a .env file with: DISCORD_TOKEN=your_token_here"
        )
    
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
