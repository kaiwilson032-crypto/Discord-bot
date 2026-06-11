"""
Discord Bot with Slash Commands + Application System + Modal Batching
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
            current_batch_index INTEGER,
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
    def start_application(user_id: int, guild_id: int):
        """Start a new application for user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO active_applications (user_id, guild_id, current_batch_index, answers)
            VALUES (?, ?, 0, '[]')
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                current_batch_index = 0,
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
            SELECT current_batch_index, answers
            FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "batch_index": result[0],
                "answers": json.loads(result[1])
            }
        return None
    
    @staticmethod
    def add_answers(user_id: int, guild_id: int, new_answers: List[str]) -> int:
        """Add batch of answers and increment batch index. Returns next batch index"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current state
        cursor.execute("""
            SELECT current_batch_index, answers
            FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return -1
        
        batch_index, answers_json = result
        answers = json.loads(answers_json)
        
        # Add new answers
        answers.extend(new_answers)
        
        # Increment batch index
        next_batch = batch_index + 1
        
        # Update database
        cursor.execute("""
            UPDATE active_applications
            SET current_batch_index = ?, answers = ?
            WHERE user_id = ? AND guild_id = ?
        """, (next_batch, json.dumps(answers), user_id, guild_id))
        
        conn.commit()
        conn.close()
        return next_batch
    
    @staticmethod
    def delete_application(user_id: int, guild_id: int):
        """Delete application"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM active_applications WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        conn.commit()
        conn.close()


# -------------------------
# CUSTOM MODAL FOR BATCH QUESTIONS
# -------------------------

class ApplicationModal(discord.ui.Modal):
    """Modal for collecting batch of application answers"""
    
    def __init__(self, user_id: int, guild_id: int, all_questions: List[str], 
                 question_indices: List[int], batch_number: int, total_batches: int):
        super().__init__(title=f"Application - Batch {batch_number}/{total_batches}")
        
        self.user_id = user_id
        self.guild_id = guild_id
        self.all_questions = all_questions
        self.question_indices = question_indices
        self.batch_number = batch_number
        self.total_batches = total_batches
        
        # Add text input for each question in this batch
        for idx in question_indices:
            question = all_questions[idx]
            # Create label that fits Discord's 45 character limit
            label = f"Q{idx + 1}"
            
            text_input = discord.ui.TextInput(
                label=label,
                placeholder=question[:100] if len(question) > 100 else question,
                required=True,
                style=discord.TextStyle.paragraph,
                min_length=1,
                max_length=1000
            )
            self.add_item(text_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        
        try:
            # Defer the response first to prevent timeout
            await interaction.response.defer(thinking=True)
            
            # Collect answers from all inputs
            answers = [item.value for item in self.children if isinstance(item, discord.ui.TextInput)]
            
            # Add answers to database
            next_batch_index = ApplicationDB.add_answers(self.user_id, self.guild_id, answers)
            
            if next_batch_index == -1:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Failed to save answers. Please try again.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Check if there are more batches
            if next_batch_index < self.total_batches:
                # Show next batch
                start_idx = next_batch_index * 5
                end_idx = min(start_idx + 5, len(self.all_questions))
                next_question_indices = list(range(start_idx, end_idx))
                
                embed = discord.Embed(
                    title="✅ Batch Submitted",
                    description=f"Answers saved! Proceeding to batch {next_batch_index + 1}/{self.total_batches}...",
                    color=discord.Color.green()
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                next_modal = ApplicationModal(
                    self.user_id,
                    self.guild_id,
                    self.all_questions,
                    next_question_indices,
                    next_batch_index + 1,
                    self.total_batches
                )
                await interaction.followup.send_modal(next_modal)
            else:
                # All batches complete - submit application
                embed = discord.Embed(
                    title="✅ Application Complete",
                    description="All questions answered! Submitting your application...",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Get all answers
                app_data = ApplicationDB.get_application(self.user_id, self.guild_id)
                all_answers = app_data["answers"] if app_data else []
                
                # Send to target channel
                await send_application_to_channel(
                    self.guild_id,
                    interaction.user,
                    self.all_questions,
                    all_answers
                )
                
                # Set cooldown
                ApplicationDB.set_cooldown(self.user_id, self.guild_id)
                
                # Delete application
                ApplicationDB.delete_application(self.user_id, self.guild_id)
                
                # Send confirmation
                confirm_embed = discord.Embed(
                    title="✅ Application Submitted",
                    description="Your application has been submitted! Thank you for applying.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=confirm_embed, ephemeral=True)
        
        except Exception as e:
            print(f"Error in modal submission: {e}")
            try:
                await interaction.followup.send(
                    f"❌ An error occurred: {str(e)}",
                    ephemeral=True
                )
            except:
                pass


# -------------------------
# HELPER FUNCTIONS
# -------------------------

async def send_application_to_channel(guild_id: int, user: discord.User, questions: List[str], answers: List[str]):
    """Send submitted application to target channel"""
    
    target_channel_id = ApplicationDB.get_target_channel(guild_id)
    
    guild = bot.get_guild(guild_id)
    
    if not guild:
        return
    
    # Try to find specified channel, fallback to #applications or first text channel
    target_channel = None
    
    if target_channel_id:
        target_channel = guild.get_channel(target_channel_id)
    
    if not target_channel:
        target_channel = discord.utils.get(guild.text_channels, name="applications")
    
    if not target_channel:
        target_channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
    
    if not target_channel:
        return
    
    # Build application embed
    embed = discord.Embed(
        title=f"📋 New Application from {user}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="User ID", value=user.id, inline=True)
    
    # Add Q&A pairs
    for i, (question, answer) in enumerate(zip(questions, answers)):
        # Truncate if too long for embed
        q_display = question[:100] if len(question) > 100 else question
        a_display = answer[:300] if len(answer) > 300 else answer
        embed.add_field(name=f"Q{i+1}: {q_display}", value=a_display, inline=False)
    
    embed.set_footer(text=f"Submitted at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    try:
        await target_channel.send(embed=embed)
    except Exception as e:
        print(f"Error sending application to channel: {e}")


# -------------------------
# FLASK KEEP-ALIVE (for Render.com)
# -------------------------

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    """Run Flask server on port 5000"""
    flask_app.run(host='0.0.0.0', port=5000, debug=False)

# -------------------------
# BOT SETUP
# -------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize database on startup
@bot.event
async def on_ready():
    init_db()
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"✅ Bot logged in as {bot.user}")


# -------------------------
# GENERAL COMMANDS
# -------------------------

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    """Ping command"""
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {round(bot.latency * 1000)}ms",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="hello", description="Get a greeting from the bot")
async def hello(interaction: discord.Interaction):
    """Hello command"""
    embed = discord.Embed(
        title=f"👋 Hello {interaction.user.name}!",
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
    embed.add_field(name="Target Channel", value=target_channel.mention if target_channel else "Auto-detect (#applications or first channel)", inline=True)
    embed.add_field(name="Questions:", value="\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)]), inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="application", description="Start an application")
async def application(interaction: discord.Interaction):
    """Start the application process with modals (batched 5 questions at a time)"""
    
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
    ApplicationDB.start_application(interaction.user.id, interaction.guild.id)
    
    # Calculate batches (5 questions per batch)
    batch_size = 5
    total_batches = (len(questions) + batch_size - 1) // batch_size  # Ceiling division
    
    # Show first batch
    question_indices = list(range(0, min(batch_size, len(questions))))
    
    modal = ApplicationModal(
        interaction.user.id,
        interaction.guild.id,
        questions,
        question_indices,
        batch_number=1,
        total_batches=total_batches
    )
    await interaction.response.send_modal(modal)


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
        # Calculate progress in terms of answered questions
        answered = len(app_data["answers"])
        total = len(questions)
        batch_index = app_data["batch_index"]
        
        embed = discord.Embed(
            title="📋 Application Status",
            description=f"Progress: **{answered}/{total}** questions answered\nCurrent Batch: **{batch_index + 1}**",
            color=discord.Color.blue()
        )
        
        # Show next unanswered question
        if answered < total:
            embed.add_field(name="Next Question", value=questions[answered], inline=False)
        else:
            embed.add_field(name="Status", value="All questions answered! Waiting to submit...", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------------
# START BOT
# -------------------------
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    # Start Flask server in background thread (for Render.com keep-alive)
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("✅ Flask server started on port 5000")
    
    # Start Discord bot
    bot.run(token)
