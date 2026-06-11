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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_settings (
            guild_id INTEGER PRIMARY KEY,
            questions TEXT,
            target_channel_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cooldowns (
            user_id INTEGER,
            guild_id INTEGER,
            last_application TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )
    """)
    
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT target_channel_id FROM server_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    @staticmethod
    def check_cooldown(user_id: int, guild_id: int, cooldown_minutes: int = 5) -> bool:
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
        return max(0, cooldown_minutes * 60 - int(time_elapsed.total_seconds()))

    @staticmethod
    def set_cooldown(user_id: int, guild_id: int):
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
    def get_application(user_id: int, guild_id: int):
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
            return {"question_index": result[0], "answers": json.loads(result[1])}
        return None

    @staticmethod
    def add_answer(user_id: int, guild_id: int, answer: str) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT current_question_index, answers
            FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return -1

        index, answers_json = result
        answers = json.loads(answers_json)
        answers.append(answer)

        new_index = index + 1

        cursor.execute("""
            UPDATE active_applications
            SET current_question_index = ?, answers = ?
            WHERE user_id = ? AND guild_id = ?
        """, (new_index, json.dumps(answers), user_id, guild_id))

        conn.commit()
        conn.close()
        return new_index

    @staticmethod
    def get_application_data(user_id: int, guild_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT answers FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()

        return {"answers": json.loads(result[0])} if result else None

    @staticmethod
    def delete_application(user_id: int, guild_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM active_applications
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        conn.commit()
        conn.close()

# -------------------------
# KEEP ALIVE FIX (CLEAN)
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
    t.daemon = True
    t.start()

# -------------------------
# DISCORD BOT SETUP
# -------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

init_db()

# -------------------------
# EVENTS
# -------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    app_data = ApplicationDB.get_application(message.author.id, message.guild.id)
    if not app_data:
        return

    questions = ApplicationDB.get_questions(message.guild.id)
    if not questions:
        return

    answer = message.content
    await message.delete()

    next_index = ApplicationDB.add_answer(message.author.id, message.guild.id, answer)

    if next_index >= len(questions):
        await submit_application(message.author, message.guild, questions)
        ApplicationDB.delete_application(message.author.id, message.guild.id)
        ApplicationDB.set_cooldown(message.author.id, message.guild.id)
    else:
        embed = discord.Embed(
            title=f"Question {next_index+1}/{len(questions)}",
            description=questions[next_index],
            color=discord.Color.blue()
        )
        await message.channel.send(embed=embed)

# (KEEP ALL YOUR COMMANDS EXACTLY THE SAME — unchanged below)
# I did NOT modify them to avoid breaking your system.

# -------------------------
# START BOT (FIXED ORDER)
# -------------------------
if __name__ == "__main__":
    keep_alive()  # ✅ ONLY IMPORTANT FIX HERE

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN not found")

    bot.run(token)
