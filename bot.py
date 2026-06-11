"""
Discord Bot with Slash Commands + Application System + Render Keep Alive Fix
"""

import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List

# Load environment variables
load_dotenv()

# -------------------------
# DATABASE SETUP
# -------------------------
DB_PATH = "bot_data.db"

def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for server application settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_settings (
            guild_id INTEGER PRIMARY KEY,
            questions TEXT,
            target_channel_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table for user cooldowns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cooldowns (
            user_id INTEGER,
            guild_id INTEGER,
            last_application TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )
    """)
    
    # Table for tracking active applications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_applications (
            user_id INTEGER,
            guild_id INTEGER,
            current_question_index INTEGER,
            answers TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )
    """)
    
    conn.commit()
    conn.close()

class ApplicationDB:
    """Database helper class for application system"""
    
    @staticmethod
    def get_questions(guild_id: int) -> Optional[List[str]]:
        """Get questions for a server"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT questions FROM server_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return json.loads(result[0])
        return None
    
    @staticmethod
    def set_questions(guild_id: int, questions: List[str], target_channel_id: int):
        """Set questions for a server (overwrites previous)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        questions_json = json.dumps(questions)
        
        cursor.execute("""
            INSERT INTO server_settings (guild_id, questions, target_channel_id, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET 
                questions = excluded.questions,
                target_channel_id = excluded.target_channel_id,
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, questions_json, target_channel_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_target_channel(guild_id: int) -> Optional[int]:
        """Get target channel for applications"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT target_channel_id FROM server_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    @staticmethod
    def check_cooldown(user_id: int, guild_id: int, cooldown_minutes: int = 5) -> bool:
        """Check if user is on cooldown. Returns True if they can apply, False if on cooldown"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_application FROM user_cooldowns WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return True
        
        last_time = datetime.fromisoformat(result[0])
        return datetime.utcnow() >= last_time + timedelta(minutes=cooldown_minutes)
    
    @staticmethod
    def get_cooldown_remaining(user_id: int, guild_id: int, cooldown_minutes: int = 5) -> int:
        """Get remaining cooldown in seconds"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_application FROM user_cooldowns WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return 0
        
        last_time = datetime.fromisoformat(result[0])
        time_elapsed = datetime.utcnow() - last_time
        cooldown_seconds = cooldown_minutes * 60
        remaining = cooldown_seconds - int(time_elapsed.total_seconds())
        return max(0, remaining)
    
    @staticmethod
    def set_cooldown(user_id: int, guild_id: int):
        """Set cooldown for user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_cooldowns (user_id, guild_id, last_application)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                last_application = CURRENT_TIMESTAMP
        """, (user_id, guild_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def start_application(user_id: int, guild_id: int, questions: List[str]):
        """Start a new application for user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO active_applications (user_id, guild_id, current_question_index, answers)
            VALUES (?, ?, 0, '[]')
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                current_question_index = 0,
                answers = '[]',
                started_at = CURRENT_TIMESTAMP
        """, (user_id, guild_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_application(user_id: int, guild_id: int) -> Optional[dict]:
        """Get active application for user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT current_question_index, answers
            FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "question_index": result[0],
                "answers": json.loads(result[1])
            }
        return None
    
    @staticmethod
    def add_answer(user_id: int, guild_id: int, answer: str) -> int:
        """Add answer to current question and increment index. Returns next question index"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current state
        cursor.execute("""
            SELECT current_question_index, answers
            FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return -1
        
        question_index, answers_json = result
        answers = json.loads(answers_json)
        answers.append(answer)
        
        new_index = question_index + 1
        cursor.execute("""
            UPDATE active_applications
            SET current_question_index = ?, answers = ?
            WHERE user_id = ? AND guild_id = ?
        """, (new_index, json.dumps(answers), user_id, guild_id))
        
        conn.commit()
        conn.close()
        return new_index
    
    @staticmethod
    def get_application_data(user_id: int, guild_id: int) -> Optional[dict]:
        """Get full application data (for submission)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT answers FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {"answers": json.loads(result[0])}
        return None
    
    @staticmethod
    def delete_application(user_id: int, guild_id: int):
        """Delete active application"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        conn.commit()
        conn.close()

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
    t = Thread(target=run_web, daemon=True)
    t.start()

# Start web server first (important for Render)
keep_alive()

# -------------------------
# DISCORD BOT SETUP
# -------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Initialize database
init_db()

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

@bot.event
async def on_message(message: discord.Message):
    """Handle application answers from users"""
    if message.author.bot:
        return
    
    # Check if user has active application
    app_data = ApplicationDB.get_application(message.author.id, message.guild.id)
    if not app_data:
        return
    
    questions = ApplicationDB.get_questions(message.guild.id)
    if not questions:
        return
    
    # Get the answer
    answer = message.content
    await message.delete()  # Clean up
    
    # Add answer and get next question index
    next_index = ApplicationDB.add_answer(message.author.id, message.guild.id, answer)
    
    # Check if application is complete
    if next_index >= len(questions):
        # Application complete - submit it
        await submit_application(message.author, message.guild, questions)
        ApplicationDB.delete_application(message.author.id, message.guild.id)
        ApplicationDB.set_cooldown(message.author.id, message.guild.id)
    else:
        # Ask next question
        embed = discord.Embed(
            title=f"Question {next_index + 1}/{len(questions)}",
            description=questions[next_index],
            color=discord.Color.blue()
        )
        embed.set_footer(text="Reply in chat to answer this question")
        await message.channel.send(embed=embed)

# -------------------------
# HELPER FUNCTIONS
# -------------------------
async def submit_application(user: discord.User, guild: discord.Guild, questions: List[str]):
    """Submit completed application to target channel"""
    target_channel_id = ApplicationDB.get_target_channel(guild.id)
    
    # Use default "applications" channel or first available text channel
    target_channel = None
    if target_channel_id:
        target_channel = guild.get_channel(target_channel_id)
    
    if not target_channel:
        for channel in guild.text_channels:
            if "applications" in channel.name.lower():
                target_channel = channel
                break
    
    if not target_channel:
        target_channel = guild.text_channels[0] if guild.text_channels else None
    
    if not target_channel:
        return
    
    # Get answers
    app_data = ApplicationDB.get_application_data(user.id, guild.id)
    if not app_data:
        return
    
    answers = app_data["answers"]
    
    # Build embed
    embed = discord.Embed(
        title="📋 New Application Received",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Applicant", value=f"{user.mention} ({user})", inline=False)
    
    for i, (question, answer) in enumerate(zip(questions, answers)):
        embed.add_field(
            name=f"Q{i+1}: {question}",
            value=answer or "*No answer provided*",
            inline=False
        )
    
    embed.set_footer(text=f"User ID: {user.id}")
    
    try:
        await target_channel.send(embed=embed)
    except Exception as e:
        print(f"Error sending application to channel: {e}")

# -------------------------
# SLASH COMMANDS
# -------------------------

# Original commands
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
# APPLICATION SYSTEM COMMANDS
# -------------------------

@bot.tree.command(name="setup-admin", description="Configure application questions (Admin Only)")
@app_commands.describe(
    question_1="Question 1 (required)",
    question_2="Question 2 (optional)",
    question_3="Question 3 (optional)",
    question_4="Question 4 (optional)",
    question_5="Question 5 (optional)",
    question_6="Question 6 (optional)",
    question_7="Question 7 (optional)",
    question_8="Question 8 (optional)",
    question_9="Question 9 (optional)",
    question_10="Question 10 (optional)",
    target_channel="Channel to send applications to (optional - defaults to #applications)"
)
async def setup_admin(
    interaction: discord.Interaction,
    question_1: str,
    question_2: Optional[str] = None,
    question_3: Optional[str] = None,
    question_4: Optional[str] = None,
    question_5: Optional[str] = None,
    question_6: Optional[str] = None,
    question_7: Optional[str] = None,
    question_8: Optional[str] = None,
    question_9: Optional[str] = None,
    question_10: Optional[str] = None,
    target_channel: Optional[discord.TextChannel] = None
):
    """Setup application questions for the server"""
    
    # Check admin permissions
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="Only server administrators can configure applications.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Collect non-empty questions
    questions = [q for q in [question_1, question_2, question_3, question_4, question_5,
                             question_6, question_7, question_8, question_9, question_10] if q]
    
    if not questions:
        embed = discord.Embed(
            title="❌ Error",
            description="At least one question is required.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if len(questions) > 10:
        embed = discord.Embed(
            title="❌ Error",
            description="Maximum 10 questions allowed.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Determine target channel
    channel_id = target_channel.id if target_channel else None
    
    # Save to database
    ApplicationDB.set_questions(interaction.guild.id, questions, channel_id)
    
    # Confirmation embed
    embed = discord.Embed(
        title="✅ Application Setup Complete",
        color=discord.Color.green()
    )
    embed.add_field(name="Questions Set", value=len(questions), inline=True)
    embed.add_field(name="Target Channel", value=target_channel.mention if target_channel else "Auto-detect", inline=True)
    embed.add_field(name="Questions:", value="\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)]), inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="application", description="Start an application")
async def application(interaction: discord.Interaction):
    """Start the application process"""
    
    # Check if questions are configured
    questions = ApplicationDB.get_questions(interaction.guild.id)
    if not questions:
        embed = discord.Embed(
            title="❌ Applications Not Configured",
            description="Server admins have not set up application questions yet.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check cooldown
    if not ApplicationDB.check_cooldown(interaction.user.id, interaction.guild.id):
        remaining = ApplicationDB.get_cooldown_remaining(interaction.user.id, interaction.guild.id)
        mins = remaining // 60
        secs = remaining % 60
        embed = discord.Embed(
            title="⏳ On Cooldown",
            description=f"You must wait **{mins}m {secs}s** before applying again.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if already has active application
    if ApplicationDB.get_application(interaction.user.id, interaction.guild.id):
        embed = discord.Embed(
            title="❌ Active Application",
            description="You already have an active application in progress.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Start application
    ApplicationDB.start_application(interaction.user.id, interaction.guild.id, questions)
    
    # Send first question
    embed = discord.Embed(
        title=f"Question 1/{len(questions)}",
        description=questions[0],
        color=discord.Color.blue()
    )
    embed.set_footer(text="Reply in chat to answer this question")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="app-cancel", description="Cancel your active application")
async def app_cancel(interaction: discord.Interaction):
    """Cancel current application"""
    
    app_data = ApplicationDB.get_application(interaction.user.id, interaction.guild.id)
    if not app_data:
        embed = discord.Embed(
            title="❌ No Active Application",
            description="You don't have an active application to cancel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    ApplicationDB.delete_application(interaction.user.id, interaction.guild.id)
    
    embed = discord.Embed(
        title="✅ Application Cancelled",
        description="Your application has been cancelled.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="app-status", description="Check your application status")
async def app_status(interaction: discord.Interaction):
    """Check current application progress"""
    
    questions = ApplicationDB.get_questions(interaction.guild.id)
    app_data = ApplicationDB.get_application(interaction.user.id, interaction.guild.id)
    
    if not questions:
        embed = discord.Embed(
            title="❌ Applications Not Configured",
            description="Server admins have not set up application questions yet.",
            color=discord.Color.red()
        )
    elif not app_data:
        embed = discord.Embed(
            title="❌ No Active Application",
            description="You don't have an active application.",
            color=discord.Color.red()
        )
    else:
        progress = app_data["question_index"]
        embed = discord.Embed(
            title="📋 Application Status",
            description=f"Progress: **{progress}/{len(questions)}** questions answered",
            color=discord.Color.blue()
        )
        embed.add_field(name="Next Question", value=questions[progress] if progress < len(questions) else "Complete", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------------
# START BOT
# -------------------------
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    bot.run(token)
