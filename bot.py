"""
Discord Bot with Slash Commands + Application System + Modal Batching + Profanity Filter
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
import re
import random

# Load environment variables
load_dotenv()

# -------------------------
# PROFANITY FILTER SETUP
# -------------------------
# Words/phrases that are not allowed (racist, sexist, homophobic)
# Swearing is allowed, so common curse words are not included
BANNED_WORDS = {
    # Racist slurs and terms (all forms)
    # N-word variations - comprehensive coverage with NO LOOKAHEAD to catch all endings
    # Double-G forms with all vowel endings
    r'\bn[i!1]gg[a3e4]\b',
    r'\bn[i!1]gg[a3e4]r\b',
    r'\bn[i!1]gg[a3e4]rs?\b',
    r'\bn[i!1]gg[a3e4]rz?\b',
    r'\bn[i!1]gg[a3e4]h\b',
    r'\bn[i!1]gg[a3e4]hs?\b',
    r'\bn[i!1]gg[a3e4]hz?\b',
    r'\bn[i!1]gg[a3e4]ing\b',
    r'\bn[i!1]gg[a3e4]ify\b',
    r'\bn[i!1]gg[a3e4]fied\b',
    r'\bn[i!1]gg[a3e4]hood\b',
    # Single-G forms with all vowel endings
    r'\bn[i!1]g[a3e4]\b',
    r'\bn[i!1]g[a3e4]r\b',
    r'\bn[i!1]g[a3e4]rs?\b',
    r'\bn[i!1]g[a3e4]rz?\b',
    r'\bn[i!1]g[a3e4]h\b',
    r'\bn[i!1]g[a3e4]hs?\b',
    r'\bn[i!1]g[a3e4]hz?\b',
    r'\bn[i!1]g[a3e4]ing\b',
    # Just "Nig" alone
    r'\bn[i!1]g\b',
    # With number substitutions for G (0, 6, 9) - double G
    r'\bn[i!1][g0g6g9][g0g6g9][a3e4]\b',
    r'\bn[i!1][g0g6g9][g0g6g9][a3e4]r\b',
    r'\bn[i!1][g0g6g9][g0g6g9][a3e4]rs?\b',
    r'\bn[i!1][g0g6g9][g0g6g9][a3e4]rz?\b',
    r'\bn[i!1][g0g6g9][g0g6g9][a3e4]h\b',
    r'\bn[i!1][g0g6g9][g0g6g9][a3e4]ing\b',
    # Single G with number substitutions
    r'\bn[i!1][g0g6g9][a3e4]\b',
    r'\bn[i!1][g0g6g9][a3e4]r\b',
    r'\bn[i!1][g0g6g9][a3e4]rs?\b',
    r'\bn[i!1][g0g6g9][a3e4]h\b',
    r'\bn[i!1][g0g6g9]\b',
    # With I substitutions (1, !, l, |)
    r'\bn[i!1l|][g0g6g9][g0g6g9][a3e4]\b',
    r'\bn[i!1l|][g0g6g9][g0g6g9][a3e4]r\b',
    r'\bn[i!1l|][g0g6g9][g0g6g9][a3e4]rs?\b',
    r'\bn[i!1l|][g0g6g9][a3e4]\b',
    r'\bn[i!1l|][g0g6g9][a3e4]r\b',
    r'\bn[i!1l|]g[a3e4]\b',
    r'\bn[i!1l|]gg[a3e4]\b',
    r'\bn[i!1l|]gg[a3e4]h\b',
    # No initial vowel forms
    r'\bn[g0g6g9][g0g6g9][a3e4]\b',
    r'\bn[g0g6g9][g0g6g9][a3e4]r\b',
    r'\bn[g0g6g9]g[a3e4]\b',
    r'\bn[g0g6g9]g[a3e4]r\b',
    # Just double-G without vowel
    r'\bngg\b',
    r'\bng\b',
    
    r'\bchink\b',
    r'\bchinks?\b',
    r'\bchinkz?\b',
    r'\bchink[a3e]d\b',
    r'\bchinking\b',
    
    r'\bspic\b',
    r'\bspics?\b',
    r'\bspicz?\b',
    
    r'\bk[i!1]k[e3]\b',
    r'\bk[i!1]k[e3]s?\b',
    r'\bk[i!1]k[e3]z?\b',
    
    r'\bwop\b',
    r'\bwops?\b',
    r'\bwopz?\b',
    
    r'\brag\s?head\b',
    r'\brag\s?heads?\b',
    r'\brag\s?headz?\b',
    
    r'\btowelhead\b',
    r'\btowelheads?\b',
    r'\btowelheadz?\b',
    
    r'\bbeaner\b',
    r'\bbeaners?\b',
    r'\bbeanerz?\b',
    
    r'\bpak[i!1]\b',
    r'\bpak[i!1]s?\b',
    r'\bpak[i!1]z?\b',
    r'\bpak[i!1]stan[i!1]\b',
    
    r'\bcoon\b',
    r'\bcoons?\b',
    r'\bcoonz?\b',
    
    r'\bgook\b',
    r'\bgooks?\b',
    r'\bgookz?\b',
    
    r'\bslant\b',
    r'\bslants?\b',
    r'\bslantz?\b',
    
    r'\bwhitey\b',
    r'\bwhiteys?\b',
    r'\bwhiteyz?\b',
    
    r'\bcracker\b',
    r'\bcrackers?\b',
    r'\bcrackersz?\b',
    
    # Sexist slurs and derogatory terms (all forms)
    r'\bslut\b',
    r'\bsluts?\b',
    r'\bslutz?\b',
    r'\bslutty\b',
    r'\bsluttily\b',
    r'\bsluttiness\b',
    
    r'\bwhore\b',
    r'\bwhores?\b',
    r'\bwhorez?\b',
    r'\bwhorish\b',
    r'\bwhorishly\b',
    r'\bwhored\b',
    r'\bwhoring\b',
    
    r'\bcunt\b',
    r'\bcunts?\b',
    r'\bcuntz?\b',
    r'\bcuntish\b',
    r'\bcunted\b',
    
    r'\bbitch\b',
    r'\bbitches?\b',
    r'\bbitchez?\b',
    r'\bbitchy\b',
    r'\bbitched\b',
    r'\bbitching\b',
    r'\bbitchiness\b',
    r'\bbitchier\b',
    r'\bbitchiest\b',
    
    r'\btwat\b',
    r'\btwats?\b',
    r'\btwatz?\b',
    r'\btwatwaffles?\b',
    
    r'\btranny\b',
    r'\btrannies\b',
    r'\btrannyz?\b',
    r'\btrannied\b',
    
    r'\bwhore\b',
    r'\bwhores?\b',
    
    # Homophobic slurs and terms (all forms)
    r'\bfagg?[o0]t\b',
    r'\bfagg?[o0]ts?\b',
    r'\bfagg?[o0]tz?\b',
    r'\bfagg?[o0]try\b',
    r'\bfagg?[o0]ted\b',
    r'\bfagg?[o0]ting\b',
    r'\bfagg?[o0]ish\b',
    
    r'\bf[a4]g\b',
    r'\bf[a4]gs?\b',
    r'\bf[a4]gz?\b',
    r'\bf[a4]gy\b',
    r'\bf[a4]ged\b',
    r'\bf[a4]ging\b',
    r'\bf[a4]got\b',
    r'\bf[a4]gots?\b',
    
    r'\bgay\b',
    r'\bgays?\b',
    r'\bgayz?\b',
    r'\bgayest\b',
    r'\bgayness\b',
    r'\bgayed\b',
    r'\bgay[i!1]ng\b',
    r'\bga[y1!i]\b',
    
    r'\blesbo\b',
    r'\blesbos?\b',
    r'\blesboz?\b',
    r'\blesbo[a]n\b',
    r'\blesbians?\b',
    
    r'\bdyke\b',
    r'\bdykes?\b',
    r'\bdykez?\b',
    r'\bdyked\b',
    r'\bdyking\b',
    
    r'\bqueer\b',
    r'\bqueers?\b',
    r'\bqueerz?\b',
    r'\bqueerish\b',
    r'\bqueered\b',
    r'\bqueering\b',
    r'\bqueerness\b',
    
    r'\bpoof\b',
    r'\bpoofs?\b',
    r'\bpoofz?\b',
    r'\bpoofy\b',
    
    r'\bshirtlifter\b',
    r'\bshirtlifters?\b',
    r'\bshirtlifterz?\b',
    
    r'\bsodomite\b',
    r'\bsodomites?\b',
    r'\bsodomitez?\b',
    
    r'\bpoof?\s?ter\b',
    r'\bpoof?\s?ters?\b',
}

def contains_banned_content(text: str) -> bool:
    """Check if text contains banned words/phrases"""
    text_lower = text.lower()
    for pattern in BANNED_WORDS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            print(f"[FILTER] Caught banned word with pattern: {pattern} in text: {text}")
            return True
    return False

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
    
    # Table for realm code settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS realm_codes (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


class RealmCodeDB:
    """Database helper class for realm code system"""
    
    @staticmethod
    def set_channel(guild_id: int, channel_id: int):
        """Set the realm code channel for a server"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO realm_codes (guild_id, channel_id, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = ?,
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, channel_id, channel_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_channel(guild_id: int) -> Optional[int]:
        """Get the realm code channel for a server"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM realm_codes WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    
    @staticmethod
    def delete_channel(guild_id: int):
        """Delete the realm code channel for a server"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM realm_codes WHERE guild_id = ?", (guild_id,))
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
            if self.batch_number < self.total_batches:
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
intents.message_content = True  # Required to read message content
intents.members = True  # For member info
intents.messages = True  # For message events
intents.guilds = True  # For guild info

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# MESSAGE FILTER EVENT
# -------------------------

@bot.event
async def on_message(message: discord.Message):
    """Monitor all messages for banned content"""
    
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Ignore DMs (optional - set to False to also scan DMs)
    if not message.guild:
        return
    
    # Scan the main message content
    content_to_scan = message.content.strip()
    
    # Also scan embeds if present
    if message.embeds:
        for embed in message.embeds:
            if embed.title:
                content_to_scan += " " + embed.title
            if embed.description:
                content_to_scan += " " + embed.description
            for field in embed.fields:
                if field.name:
                    content_to_scan += " " + field.name
                if field.value:
                    content_to_scan += " " + field.value
    
    print(f"[SCAN] Checking message from {message.author} in #{message.channel}: {content_to_scan[:100]}")
    
    # Check for banned content
    if content_to_scan and contains_banned_content(content_to_scan):
        print(f"[FILTER TRIGGERED] Banned content detected in message from {message.author}")
        try:
            # Check if bot has permission to delete
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                print(f"[FILTER] ❌ No permission to delete messages in {message.channel.name}")
                # Try to at least warn in the channel
                try:
                    embed = discord.Embed(
                        title="⚠️ Message Contains Inappropriate Language",
                        description=f"{message.author.mention}, your message was removed due to inappropriate content. Please review our community guidelines.",
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=embed, delete_after=10)
                except:
                    pass
                return
            
            # Delete the message
            await message.delete()
            print(f"[FILTER] ✅ Deleted message from {message.author}")
            
            # Send DM to user
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Message Deleted",
                    description="Your message was deleted for containing inappropriate language (racist, sexist, or homophobic content).",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Server", value=message.guild.name, inline=False)
                dm_embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                dm_embed.add_field(name="Reason", value="Inappropriate language detected", inline=False)
                
                await message.author.send(embed=dm_embed)
                print(f"[FILTER] DM sent to {message.author}")
            except discord.Forbidden:
                # Can't DM user, send message in channel
                try:
                    embed = discord.Embed(
                        title="⚠️ Message Deleted",
                        description=f"{message.author.mention}, your message was deleted for containing inappropriate language.",
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=embed, delete_after=10)
                except Exception as e:
                    print(f"[FILTER] Error sending deletion notice: {e}")
        except Exception as e:
            print(f"[FILTER ERROR] Failed to process banned content: {e}")
    
    # Check if someone is asking about realm code
    message_lower = message.content.lower()
    
    # More flexible keyword matching
    has_realm_keyword = any(keyword in message_lower for keyword in ["realm", "code", "realm code"])
    has_asking_keyword = any(keyword in message_lower for keyword in ["where", "what", "how", "find", "get", "need", "looking", "?"])
    
    print(f"[REALM CHECK] Message from {message.author}: '{message.content[:50]}' | Realm: {has_realm_keyword} | Asking: {has_asking_keyword}")
    
    if has_realm_keyword and has_asking_keyword:
        print(f"[REALM CODE TRIGGER] {message.author} asked about realm code in #{message.channel}")
        
        # Use thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        channel_id = await loop.run_in_executor(None, RealmCodeDB.get_channel, message.guild.id)
        
        if channel_id:
            try:
                channel = message.guild.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="🔐 Realm Code Location",
                        description=f"The realm code is located in {channel.mention}",
                        color=discord.Color.blue()
                    )
                    await message.reply(embed=embed)
                    print(f"[REALM CODE] ✅ Replied with realm code location")
                else:
                    print(f"[REALM CODE] Channel ID {channel_id} not found")
            except Exception as e:
                print(f"[REALM CODE ERROR] Failed to respond to realm code question: {e}")
        else:
            print(f"[REALM CODE] No realm code configured for this server")
    
    # Process commands normally
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """Check edited messages for banned content"""
    print(f"[EDIT DETECTED] {after.author} edited message in #{after.channel}")
    
    # Ignore bot messages
    if after.author.bot:
        return
    
    # Ignore DMs
    if not after.guild:
        return
    
    # Check if content changed
    if before.content == after.content:
        return
    
    # Scan the edited content
    content_to_scan = after.content.strip()
    
    print(f"[SCAN EDIT] Checking edited message: {content_to_scan[:100]}")
    
    # Check for banned content in the edit
    if content_to_scan and contains_banned_content(content_to_scan):
        print(f"[FILTER TRIGGERED ON EDIT] Banned content in edited message from {after.author}")
        try:
            # Check if bot has permission to delete
            if not after.channel.permissions_for(after.guild.me).manage_messages:
                print(f"[FILTER] ❌ No permission to delete edited message in {after.channel.name}")
                return
            
            # Delete the edited message
            await after.delete()
            print(f"[FILTER] ✅ Deleted edited message from {after.author}")
            
            # Send DM to user
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Edited Message Deleted",
                    description="Your edited message was deleted for containing inappropriate language.",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Server", value=after.guild.name, inline=False)
                dm_embed.add_field(name="Channel", value=after.channel.mention, inline=False)
                
                await after.author.send(embed=dm_embed)
            except discord.Forbidden:
                try:
                    embed = discord.Embed(
                        title="⚠️ Edited Message Deleted",
                        description=f"{after.author.mention}, your edited message was deleted for containing inappropriate language.",
                        color=discord.Color.red()
                    )
                    await after.channel.send(embed=embed, delete_after=10)
                except Exception as e:
                    print(f"[FILTER] Error sending deletion notice: {e}")
        except Exception as e:
            print(f"[FILTER ERROR] Failed to process edited message: {e}")

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

@bot.tree.command(name="goose", description="Get a random funny goose message")
async def goose(interaction: discord.Interaction):
    """Send a random goose message - text only"""
    
    try:
        goose_messages = [
            "🦆 HONK HONK! 🦆\nHere's a silly goose for you!",
            "🦆 HONK HONK! 🦆\n*aggressive honking noises*",
            "🦆 HONK HONK! 🦆\nGoose committee approves this message!",
            "🦆 HONK HONK! 🦆\nA wild goose appears!",
            "🦆 HONK HONK! 🦆\nThe goose has spoken!",
            "🦆 HONK HONK! 🦆\nGoose energy detected!",
            "🦆 HONK HONK! 🦆\nThis goose slaps!",
            "🦆 HONK HONK! 🦆\nPeace was never an option!",
        ]
        
        random_message = random.choice(goose_messages)
        
        # Send as plain text only - NO EMBEDS, NO IMAGES
        await interaction.response.send_message(random_message)
    except Exception as e:
        await interaction.response.send_message(f"🦆 HONK HONK! 🦆\nError: {str(e)}", ephemeral=True)


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
    target_channel="Channel to send applications to (optional - defaults to #applications)"
)
async def setup_admin(
    interaction: discord.Interaction,
    question_1: str,
    question_2: Optional[str] = None,
    question_3: Optional[str] = None,
    question_4: Optional[str] = None,
    question_5: Optional[str] = None,
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
    questions = [q for q in [question_1, question_2, question_3, question_4, question_5] if q]
    
    if not questions:
        embed = discord.Embed(
            title="❌ Error",
            description="At least one question is required.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if len(questions) > 5:
        embed = discord.Embed(
            title="❌ Error",
            description="Maximum 5 questions allowed.",
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


@bot.tree.command(name="set-realm-code", description="Set the channel where the realm code is located (Admin Only)")
@app_commands.describe(
    channel="The channel containing the realm code"
)
async def set_realm_code(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):
    """Set the realm code channel for the server"""
    
    try:
        # Defer FIRST before doing anything else
        await interaction.response.defer(ephemeral=True)
        
        # Check admin permissions
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only server administrators can set the realm code channel.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Run database operation in thread pool to prevent blocking
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, RealmCodeDB.set_channel, interaction.guild.id, channel.id)
        
        # Confirmation embed
        embed = discord.Embed(
            title="✅ Realm Code Channel Set",
            description=f"Realm code channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel", value=channel.name, inline=True)
        embed.add_field(name="Channel ID", value=channel.id, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"[REALM CODE] ✅ Admin {interaction.user} set realm code channel to {channel.name}")
    except Exception as e:
        print(f"[REALM CODE ERROR] {str(e)}")
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except Exception as follow_error:
            print(f"[REALM CODE ERROR] Could not send error message: {str(follow_error)}")


@bot.tree.command(name="realm-code", description="Get the realm code location")
async def realm_code(interaction: discord.Interaction):
    """Tell user where to find the realm code"""
    
    try:
        # Check if command is in a server
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in a server.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Defer to prevent timeout
        await interaction.response.defer()
        
        print(f"[REALM CODE CMD] {interaction.user} requested realm code in server {interaction.guild.name} (ID: {interaction.guild.id})")
        
        # Get the realm code channel
        channel_id = RealmCodeDB.get_channel(interaction.guild.id)
        
        if not channel_id:
            print(f"[REALM CODE CMD] No realm code configured for server {interaction.guild.id}")
            embed = discord.Embed(
                title="❌ Realm Code Not Configured",
                description="The server admin hasn't set up the realm code location yet.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        print(f"[REALM CODE CMD] Found channel ID: {channel_id}")
        
        # Get the channel object
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            print(f"[REALM CODE CMD] Channel {channel_id} not found in server")
            embed = discord.Embed(
                title="❌ Channel Not Found",
                description="The realm code channel has been deleted or moved.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        print(f"[REALM CODE CMD] Sending realm code location to {interaction.user}")
        embed = discord.Embed(
            title="🔐 Realm Code Location",
            description=f"The realm code is located in {channel.mention}",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"[REALM CODE CMD ERROR] {str(e)}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass


@bot.tree.command(name="realm-code-debug", description="Check realm code setup (Admin Only)")
async def realm_code_debug(interaction: discord.Interaction):
    """Debug realm code settings"""
    
    try:
        # Check admin permissions
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only server administrators can use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Defer to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        print(f"[DEBUG] Admin {interaction.user} checking realm code setup in {interaction.guild.name}")
        
        channel_id = RealmCodeDB.get_channel(interaction.guild.id)
        
        if not channel_id:
            embed = discord.Embed(
                title="❌ Not Configured",
                description="Realm code channel not configured. Use `/set-realm-code` to set it up.",
                color=discord.Color.orange()
            )
        else:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="✅ Realm Code Configured",
                    description=f"Channel: {channel.mention}\nChannel ID: {channel_id}",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Channel Not Found",
                    description=f"Channel ID {channel_id} stored but channel doesn't exist. Reconfigure with `/set-realm-code`",
                    color=discord.Color.orange()
                )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"[DEBUG ERROR] {str(e)}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass


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
