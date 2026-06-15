"""
Discord Bot with Slash Commands + Application System + Modal Batching + Profanity Filter
"""

import discord
from discord.ext import commands, tasks
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
import asyncio

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    print("[FIREBASE] Firebase SDK not installed. Install with: pip install firebase-admin")
    FIREBASE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Initialize Firebase
firebase_db = None
if FIREBASE_AVAILABLE:
    try:
        firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
        if firebase_creds:
            # Parse JSON credentials from environment variable
            creds_dict = json.loads(firebase_creds)
            creds = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(creds)
            firebase_db = firestore.client()
            print("[FIREBASE] ✅ Firebase initialized successfully")
        else:
            print("[FIREBASE] ⚠️  FIREBASE_CREDENTIALS not in .env, using SQLite")
    except Exception as e:
        print(f"[FIREBASE] Error: {str(e)} - Using SQLite fallback")

# Dragon Rider System
try:
    from dragon_system import DragonSystem
    DRAGON_SYSTEM_AVAILABLE = True
    print("[DRAGON] ✅ Dragon system loaded")
except ImportError as e:
    print(f"[DRAGON] ⚠️  Dragon system not found: {str(e)}")
    DRAGON_SYSTEM_AVAILABLE = False

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
# DATABASE SETUP
# -------------------------
DB_PATH = "bot_data.db"
SEED_DB_PATH = "bot_data_seed.db"

def init_database_from_seed():
    """Initialize database from seed file if it doesn't exist"""
    import os
    import shutil
    
    if not os.path.exists(DB_PATH):
        if os.path.exists(SEED_DB_PATH):
            print(f"[DB INIT] 📦 Initializing from seed database...")
            shutil.copy(SEED_DB_PATH, DB_PATH)
            print(f"[DB INIT] ✅ Database initialized from seed - all settings restored!")
        else:
            print(f"[DB INIT] 🆕 No seed found, creating new database...")
            init_db()
    else:
        print(f"[DB INIT] ✅ Using existing database")


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
    
    # Table for giveaway settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaway_settings (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table for active giveaways
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            giveaway_id TEXT PRIMARY KEY,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            prize TEXT NOT NULL,
            days INTEGER NOT NULL,
            winners INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_at TIMESTAMP NOT NULL,
            ended INTEGER DEFAULT 0
        )
    """)
    
    # Table for giveaway entries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaway_entries (
            giveaway_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (giveaway_id, user_id),
            FOREIGN KEY (giveaway_id) REFERENCES giveaways(giveaway_id)
        )
    """)
    
    conn.commit()
    conn.close()

class ApplicationDB:
    """Database helper class for application system - Uses Firebase with SQLite fallback"""
    
    @staticmethod
    def get_questions(guild_id: int) -> Optional[List[str]]:
        """Get questions for a server"""
        if firebase_db:
            try:
                doc = firebase_db.collection('server_settings').document(str(guild_id)).get()
                if doc.exists:
                    questions = doc.get('questions')
                    return questions if questions else None
            except Exception as e:
                print(f"[FIREBASE] Error getting questions: {str(e)}")
        
        # Fallback to SQLite
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
        if firebase_db:
            try:
                firebase_db.collection('server_settings').document(str(guild_id)).set({
                    'guild_id': guild_id,
                    'questions': questions,
                    'target_channel_id': target_channel_id,
                    'updated_at': datetime.utcnow()
                })
                print(f"[FIREBASE] ✅ Questions saved for guild {guild_id}")
                return
            except Exception as e:
                print(f"[FIREBASE] Error saving: {str(e)}")
        
        # Fallback to SQLite
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
        print(f"[SQLITE] ✅ Questions saved for guild {guild_id}")
    
    @staticmethod
    def get_target_channel(guild_id: int) -> Optional[int]:
        """Get target channel for applications"""
        if firebase_db:
            try:
                doc = firebase_db.collection('server_settings').document(str(guild_id)).get()
                if doc.exists:
                    return doc.get('target_channel_id')
            except Exception as e:
                print(f"[FIREBASE] Error getting channel: {str(e)}")
        
        # Fallback to SQLite
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
    """Database helper class for realm code system - Uses Firebase with SQLite fallback"""
    
    @staticmethod
    def set_channel(guild_id: int, channel_id: int):
        """Set the realm code channel for a server"""
        if firebase_db:
            try:
                firebase_db.collection('realm_codes').document(str(guild_id)).set({
                    'guild_id': guild_id,
                    'channel_id': channel_id,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                print(f"[FIREBASE] ✅ Realm code saved for guild {guild_id}")
                return
            except Exception as e:
                print(f"[FIREBASE] Error saving: {str(e)}")
        
        # Fallback to SQLite
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
        print(f"[SQLITE] ✅ Realm code saved for guild {guild_id}")
    
    @staticmethod
    def get_channel(guild_id: int) -> Optional[int]:
        """Get the realm code channel for a server"""
        if firebase_db:
            try:
                doc = firebase_db.collection('realm_codes').document(str(guild_id)).get()
                if doc.exists:
                    return doc.get('channel_id')
            except Exception as e:
                print(f"[FIREBASE] Error getting: {str(e)}")
        
        # Fallback to SQLite
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
        if firebase_db:
            try:
                firebase_db.collection('realm_codes').document(str(guild_id)).delete()
                print(f"[FIREBASE] ✅ Realm code deleted for guild {guild_id}")
                return
            except Exception as e:
                print(f"[FIREBASE] Error deleting: {str(e)}")
        
        # Fallback to SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM realm_codes WHERE guild_id = ?", (guild_id,))
        conn.commit()
        conn.close()


class GiveawaySettingsDB:
    """Database helper for giveaway channel settings"""
    
    @staticmethod
    def set_channel(guild_id: int, channel_id: int):
        """Set giveaway channel"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO giveaway_settings (guild_id, channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET channel_id = ?
        """, (guild_id, channel_id, channel_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_channel(guild_id: int) -> Optional[int]:
        """Get giveaway channel"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM giveaway_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None


class GiveawayDB:
    """Database helper for active giveaways"""
    
    @staticmethod
    def create(giveaway_id: str, guild_id: int, channel_id: int, message_id: int, prize: str, days: int, winners: int, host_id: int, end_at: datetime):
        """Create new giveaway"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO giveaways (giveaway_id, guild_id, channel_id, message_id, prize, days, winners, host_id, end_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (giveaway_id, guild_id, channel_id, message_id, prize, days, winners, host_id, end_at))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get(giveaway_id: str) -> Optional[dict]:
        """Get giveaway details"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM giveaways WHERE giveaway_id = ?", (giveaway_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'giveaway_id': result[0],
                'guild_id': result[1],
                'channel_id': result[2],
                'message_id': result[3],
                'prize': result[4],
                'days': result[5],
                'winners': result[6],
                'host_id': result[7],
                'created_at': result[8],
                'end_at': result[9],
                'ended': result[10]
            }
        return None
    
    @staticmethod
    def add_entry(giveaway_id: str, user_id: int):
        """Add user to giveaway"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO giveaway_entries (giveaway_id, user_id)
                VALUES (?, ?)
            """, (giveaway_id, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Already entered
    
    @staticmethod
    def remove_entry(giveaway_id: str, user_id: int):
        """Remove user from giveaway"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ?", (giveaway_id, user_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_entries(giveaway_id: str) -> List[int]:
        """Get all users entered in giveaway"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?", (giveaway_id,))
        results = cursor.fetchall()
        conn.close()
        return [r[0] for r in results]
    
    @staticmethod
    def end_giveaway(giveaway_id: str):
        """Mark giveaway as ended"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE giveaways SET ended = 1 WHERE giveaway_id = ?", (giveaway_id,))
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
# DISCORD UI COMPONENTS
# -------------------------

class ResetView(discord.ui.View):
    def __init__(self, user_id: int, timeout=30):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.confirmed = None
    
    @discord.ui.button(label="✅ Yes, Delete Everything", style=discord.ButtonStyle.danger, custom_id="reset_yes")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return
        
        try:
            DragonSystem.reset_progress(self.user_id)
            self.confirmed = True
            await interaction.response.edit_message(
                embed=discord.Embed(title="✅ Reset Complete", description="All your dragons and progress have been deleted.", color=discord.Color.green()),
                view=None
            )
            self.stop()
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary, custom_id="reset_no")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return
        
        try:
            self.confirmed = False
            await interaction.response.edit_message(
                embed=discord.Embed(title="❌ Reset Cancelled", description="Your progress is safe!", color=discord.Color.red()),
                view=None
            )
            self.stop()
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

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
    
    # Log every message to show we're watching all channels
    if message.guild:
        print(f"[MESSAGE] {message.author} in #{message.channel}: {message.content[:60]}")
    
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
    try:
        message_lower = message.content.lower()
        
        # All possible ways someone might ask about the realm code
        realm_asking_patterns = [
            "where realm",
            "where's realm",
            "where is realm",
            "wheres realm",
            "where code",
            "where's code",
            "where is code",
            "wheres code",
            "what realm",
            "what's realm",
            "what code",
            "what's code",
            "how realm",
            "how code",
            "find realm",
            "find code",
            "get realm",
            "get code",
            "need realm",
            "need code",
            "looking realm",
            "looking code",
            "realm code",
            "code realm",
            "realm?",
            "code?",
            "realm code?",
        ]
        
        # Check if any pattern matches
        is_asking_about_realm = any(pattern in message_lower for pattern in realm_asking_patterns)
        
        print(f"[REALM SCAN] #{message.channel} | {message.author}: '{message.content[:60]}' | Asking: {is_asking_about_realm}")
        
        if is_asking_about_realm:
            print(f"[REALM TRIGGER] ✅ {message.author} asked about realm code in #{message.channel}")
            
            if not message.guild:
                return
            
            channel_id = RealmCodeDB.get_channel(message.guild.id)
            
            if channel_id:
                realm_channel = message.guild.get_channel(channel_id)
                if realm_channel:
                    embed = discord.Embed(
                        title="🔐 Realm Code Location",
                        description=f"The realm code is located in {realm_channel.mention}",
                        color=discord.Color.blue()
                    )
                    try:
                        await message.reply(embed=embed)
                        print(f"[REALM] ✅ Replied to {message.author}")
                    except Exception as reply_error:
                        print(f"[REALM] Error replying: {str(reply_error)}")
                else:
                    print(f"[REALM] Channel {channel_id} not found in guild")
            else:
                print(f"[REALM] No realm code configured for {message.guild.name}")
    except Exception as e:
        print(f"[REALM ERROR] {type(e).__name__}: {str(e)}")
    
    # Check if someone is asking about ticket creation
    try:
        message_lower = message.content.lower()
        # Remove common punctuation for pattern matching
        message_cleaned = message_lower.replace("?", "").replace("!", "").replace(".", "").strip()
        
        # All possible ways someone might ask about creating a ticket
        ticket_asking_patterns = [
            "how create ticket",
            "how do i create ticket",
            "how to create ticket",
            "how make ticket",
            "how do i make ticket",
            "how to make ticket",
            "how do you make ticket",
            "how do you create ticket",
            "create ticket",
            "make ticket",
            "open ticket",
            "how open ticket",
            "how do i open ticket",
            "how to open ticket",
            "how do you open ticket",
            "ticket help",
            "help ticket",
            "how ticket",
            "where ticket",
            "find ticket",
            "get ticket",
            "need ticket",
            "looking ticket",
            "ticket",
            "create support ticket",
            "open support ticket",
            "new ticket",
            "how new ticket",
            "how do i new ticket",
            "how to new ticket",
        ]
        
        # Check if any pattern matches in cleaned message
        is_asking_about_ticket = any(pattern in message_cleaned for pattern in ticket_asking_patterns)
        
        print(f"[TICKET SCAN] #{message.channel} | {message.author}: '{message.content[:60]}' | Cleaned: '{message_cleaned[:60]}' | Asking: {is_asking_about_ticket}")
        
        if is_asking_about_ticket:
            print(f"[TICKET TRIGGER] ✅ {message.author} asked about creating a ticket in #{message.channel}")
            print(f"[TICKET TRIGGER] Original message: '{message.content}'")
            print(f"[TICKET TRIGGER] Cleaned message: '{message_cleaned}'")
            
            if not message.guild:
                print(f"[TICKET] Not in a guild, returning")
                return
            
            embed = discord.Embed(
                title="🎫 How to Create a Ticket",
                description="Go to the Important category and find 'Create a Ticket'. Click it, then create a ticket and describe what you need help with",
                color=discord.Color.gold()
            )
            try:
                await message.reply(embed=embed)
                print(f"[TICKET] ✅ Replied to {message.author}")
            except Exception as reply_error:
                print(f"[TICKET] Error replying: {str(reply_error)}")
    except Exception as e:
        print(f"[TICKET ERROR] {type(e).__name__}: {str(e)}")
    
    # Dragon Command Handler - @bot dragon [action]
    try:
        # Check if the message starts with the bot mention followed by "dragon"
        if message.content.startswith(f"{bot.user.mention} dragon"):
            # Remove the bot mention from the content to get the actual command
            content_after_mention = message.content.replace(f"{bot.user.mention}", "").strip()
            args = content_after_mention.split()
            
            if len(args) < 2:
                await message.reply("Usage: `@bot dragon [action]`\nExample: `@bot dragon hatch`\nActions: hatch, eggs, dragons, explore, train, battle, breed, island, reset, info")
                return
            
            action = args[1].lower()
            user_id = message.author.id
            guild_id = message.guild.id
        else:
            # Bot wasn't mentioned with dragon command, skip this handler
            return
        
        # Create a fake interaction-like object for reuse
        class FakeInteraction:
            def __init__(self, msg, user, guild):
                self.response = FakeResponse(msg)
                self.user = user
                self.guild = guild
        
        class FakeResponse:
            def __init__(self, msg):
                self.msg = msg
            
            async def send_message(self, embed=None, view=None, ephemeral=True):
                await self.msg.reply(embed=embed)
            
            async def edit_message(self, embed=None, view=None):
                # For battle messages, we'll handle this differently
                pass
        
        # Handle different actions
        if action == "info":
            embed = discord.Embed(
                title="🐉 Dragon Rider Game Guide",
                description="A long-term collection and progression game where you hatch, train, and battle dragons!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="🥚 Getting Started",
                value="`@bot dragon hatch` - Get a dragon egg (5 min hatch, first hatches instantly!)\n`@bot dragon eggs` - View your eggs",
                inline=False
            )
            
            embed.add_field(
                name="🐲 Main Commands",
                value="`@bot dragon dragons` - View all your dragons with stats & abilities\n`@bot dragon island` - View your resources\n`@bot dragon reset` - Reset all progress (click button to confirm)",
                inline=False
            )
            
            embed.add_field(
                name="⚔️ Action Commands",
                value="`@bot dragon explore` - Find training items (4 min cooldown)\n`@bot dragon train` - Train using items to boost stats (1 hr cooldown)\n`@bot dragon battle` - Turn-based PvE battle until someone loses",
                inline=False
            )
            
            embed.add_field(
                name="👥 PvP & Breeding",
                value="`@bot duel @user` - Challenge another player's dragon\n`@bot dragon breed` - Breed 2 dragons for offspring",
                inline=False
            )
            
            embed.add_field(
                name="📚 Information Commands",
                value="`@bot abilities` - View all dragon unique abilities\n`@bot inventory` - View training items & resources",
                inline=False
            )
            
            embed.add_field(
                name="💎 Egg Rarities",
                value="**Common** (60%) | **Rare** (25%) | **Epic** (10%) | **Legendary** (4%) | **Alpha** (1%)",
                inline=False
            )
            
            embed.add_field(
                name="❤️ Battle System",
                value="**Turn-Based Battles** - Click to attack, battles continue until HP reaches 0\n**HP System** - Based on Level + Defense + Rarity Bonus\n**Damage** - Calculated from Attack (40%) + Level (30%) + Speed (20%) + Intelligence (10%)",
                inline=False
            )
            
            embed.add_field(
                name="🎁 Training Items",
                value="Find items while exploring:\n**Common**: Dragon Scales, Fire Stones, Meat Scraps\n**Rare**: Mithril Ore, Dragon Teeth, Enchanted Herbs\n**Epic**: Legendary Gems, Phoenix Feathers, Ancient Bones\n**Legendary**: Stardust, Divine Crystals, Mythril Bars\n**Alpha**: Celestial Cores, Eternal Stones, Divine Essence",
                inline=False
            )
            
            embed.add_field(
                name="🔥 Dragon Abilities",
                value="Each dragon species has a unique ability:\n**Night Fury** - Plasma Blast\n**Red Death** - Inferno Storm\n**Bewilderbeast** - Alpha Roar\n**Stormcutter** - Lightning Strike\nAnd many more! Use `/abilities` to see all.",
                inline=False
            )
            
            embed.add_field(
                name="📊 Dragon Stats",
                value="**Attack** - Determines damage output\n**Defense** - Reduces incoming damage\n**Speed** - Affects turn order & accuracy\n**Intelligence** - Increases ability effectiveness\n**Bond** - Levels up through interaction\n**Ability Level** - Increases through training",
                inline=False
            )
            
            embed.add_field(
                name="🏆 Endgame Goals",
                value="✓ Collect every dragon species\n✓ Discover rare hybrids (5% chance from breeding)\n✓ Max all dragon stats\n✓ Reach Max Bond with dragons\n✓ Obtain Alpha Dragons\n✓ Become Dragon Master!",
                inline=False
            )
            
            await message.reply(embed=embed)
        
        elif action == "hatch":
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM dragons WHERE user_id = ?", (user_id,))
            dragon_count = cursor.fetchone()[0]
            conn.close()
            
            if dragon_count == 0:
                result = DragonSystem.create_first_egg(user_id, guild_id)
                embed = discord.Embed(
                    title="🎉 First Dragon Hatched!",
                    description=f"Species: **{result['species']}**\nRarity: **{result['rarity']}**",
                    color=discord.Color.gold()
                )
            else:
                egg = DragonSystem.hatch_new_egg(user_id, guild_id)
                embed = discord.Embed(
                    title="🥚 Egg Received!",
                    description=f"**{egg['rarity']}** rarity\n**Hatches in 5 minutes**",
                    color=discord.Color.gold()
                )
            
            await message.reply(embed=embed)
        
        elif action == "eggs":
            eggs = DragonSystem.get_eggs(user_id)
            
            if not eggs:
                embed = discord.Embed(
                    title="🥚 No Eggs",
                    description="Use `@bot dragon hatch` to get an egg!",
                    color=discord.Color.blue()
                )
            else:
                embed = discord.Embed(
                    title="🥚 Your Eggs",
                    description=f"Total: **{len(eggs)}**",
                    color=discord.Color.blue()
                )
                
                for i, (egg_id, rarity, hatch_time, is_first) in enumerate(eggs[:5], 1):
                    if is_first:
                        status = "✅ Ready!"
                    else:
                        remaining = (datetime.fromisoformat(hatch_time) - datetime.utcnow()).total_seconds()
                        if remaining > 0:
                            mins = int(remaining / 60)
                            status = f"⏳ {mins} min"
                        else:
                            status = "✅ Ready!"
                    
                    embed.add_field(name=f"{i}. {rarity} Egg", value=status, inline=True)
            
            await message.reply(embed=embed)
        
        elif action == "dragons":
            dragons = DragonSystem.get_dragons(user_id)
            
            if not dragons:
                embed = discord.Embed(
                    title="🐉 No Dragons Yet",
                    description="Use `@bot dragon hatch`!",
                    color=discord.Color.blue()
                )
            else:
                embed = discord.Embed(
                    title="🐉 Your Dragons",
                    description=f"Total: **{len(dragons)}**",
                    color=discord.Color.red()
                )
                
                for i, dragon in enumerate(dragons[:3], 1):
                    dragon_id, name, species, rarity, level, xp, attack, defense, speed, intelligence, bond, ability, hp = dragon
                    embed.add_field(
                        name=f"{i}. {species}",
                        value=f"Rarity: {rarity} | Lvl: {level}\nHP: {hp} | ⚔️ ATK: {attack} | 🛡️ DEF: {defense}",
                        inline=False
                    )
                
                await message.reply(embed=embed)
        
        elif action == "explore":
            dragons = DragonSystem.get_dragons(user_id)
            if not dragons:
                embed = discord.Embed(title="❌ No Dragons", description="Get one with `@bot dragon hatch`!", color=discord.Color.red())
            else:
                result = DragonSystem.explore(user_id, guild_id, dragons[0][0])
                if "error" in result:
                    embed = discord.Embed(title="⏳ Still Exploring", description=result["error"], color=discord.Color.orange())
                else:
                    if result['reward'] == "Training Item":
                        embed = discord.Embed(title="🌍 Found!", description=f"{result['item_name']} x{result['amount']}", color=discord.Color.green())
                    else:
                        embed = discord.Embed(title="🌍 Found!", description=f"{result['reward']} x{result['amount']}", color=discord.Color.green())
            
            await message.reply(embed=embed)
        
        elif action == "train":
            dragons = DragonSystem.get_dragons(user_id)
            if not dragons:
                embed = discord.Embed(title="❌ No Dragons", description="Get one with `@bot dragon hatch`!", color=discord.Color.red())
            else:
                result = DragonSystem.train_dragon(user_id, dragons[0][0])
                if "error" in result:
                    embed = discord.Embed(title="❌ Can't Train", description=result["error"], color=discord.Color.red())
                else:
                    embed = discord.Embed(title="🏋️ Trained!", color=discord.Color.green())
                    embed.add_field(name="Stat Boost", value=f"{result['stat']} +{result['boost']}", inline=True)
                    embed.add_field(name="Item Used", value=result['item_used'], inline=True)
            
            await message.reply(embed=embed)
        
        elif action == "breed":
            dragons = DragonSystem.get_dragons(user_id)
            if len(dragons) < 2:
                embed = discord.Embed(title="❌ Need 2 Dragons", description="You need at least 2!", color=discord.Color.red())
            else:
                result = DragonSystem.breed_dragons(user_id, dragons[0][0], dragons[1][0], guild_id)
                embed = discord.Embed(title="👶 Offspring Created!", color=discord.Color.magenta())
                embed.add_field(name="Species", value=result['species'], inline=True)
                embed.add_field(name="Rarity", value=result['rarity'], inline=True)
            
            await message.reply(embed=embed)
        
        elif action == "island":
            inv = DragonSystem.get_inventory(user_id)
            embed = discord.Embed(title="🏝️ Your Island", color=discord.Color.blue())
            embed.add_field(name="💰 Coins", value=inv['coins'], inline=True)
            embed.add_field(name="🐟 Fish", value=inv['fish'], inline=True)
            embed.add_field(name="📿 Relics", value=inv['relics'], inline=True)
            
            await message.reply(embed=embed)
        
        elif action == "battle":
            dragons = DragonSystem.get_dragons(user_id)
            if not dragons:
                embed = discord.Embed(title="❌ No Dragons", description="Get one with `@bot dragon hatch`!", color=discord.Color.red())
            else:
                result = DragonSystem.battle_pve(user_id, dragons[0][0])
                if "error" in result:
                    embed = discord.Embed(title="❌ Battle Error", description=result["error"], color=discord.Color.red())
                else:
                    winner_emoji = "🎉" if result["winner"] == "player" else "😢"
                    embed = discord.Embed(
                        title=f"{winner_emoji} Battle Complete!",
                        description=result["result"],
                        color=discord.Color.green() if result["winner"] == "player" else discord.Color.orange()
                    )
                    embed.add_field(name="Your Dragon", value=dragons[0][2], inline=True)  # species
                    embed.add_field(name="Enemy Dragon", value=result["enemy"], inline=True)
                    embed.add_field(name="Your Ability", value=result["player_ability"], inline=True)
                    embed.add_field(name="Enemy Ability", value=result["enemy_ability"], inline=True)
            
            await message.reply(embed=embed)
        
        elif action == "reset":
            embed = discord.Embed(
                title="⚠️ Delete All Progress?",
                description="This will delete all your dragons, eggs, and items. **This cannot be undone!**",
                color=discord.Color.red()
            )
            view = ResetView(user_id=user_id)
            await message.reply(embed=embed, view=view)
        
        else:
            await message.reply(f"Unknown action: `{action}`\nUse `@bot dragon info` for help!")
        
        return
    
    except Exception as e:
        print(f"[DRAGON MENTION] Error: {str(e)}")
    
    # Inventory Command Handler - @bot inventory
    try:
        if message.content.strip() == f"{bot.user.mention} inventory":
            user_id = message.author.id
            inv = DragonSystem.get_inventory(user_id)
            embed = discord.Embed(title="🎒 Your Inventory", color=discord.Color.blue())
            embed.add_field(name="💰 Coins", value=inv['coins'], inline=True)
            embed.add_field(name="🐟 Fish", value=inv['fish'], inline=True)
            embed.add_field(name="📿 Relics", value=inv['relics'], inline=True)
            
            if inv['training_items']:
                items_text = ""
                for item_name, rarity, quantity in inv['training_items']:
                    items_text += f"**{item_name}** ({rarity}) x{quantity}\n"
                embed.add_field(name="🎁 Training Items", value=items_text, inline=False)
            else:
                embed.add_field(name="🎁 Training Items", value="None yet! Explore to find items.", inline=False)
            
            await message.reply(embed=embed)
            return
    except Exception as e:
        print(f"[INVENTORY MENTION] Error: {str(e)}")
    
    # Abilities Command Handler - @bot abilities
    try:
        if message.content.strip() == f"{bot.user.mention} abilities":
            embed = discord.Embed(
                title="🐉 Dragon Abilities",
                description="Every dragon has a unique special ability!",
                color=discord.Color.red()
            )
            
            for species, ability_info in list(DragonSystem.DRAGON_ABILITIES.items())[:15]:
                embed.add_field(
                    name=f"🔥 {species}",
                    value=f"**{ability_info['name']}** - {ability_info['description']}\nPower: {ability_info['power']} | Accuracy: {ability_info['accuracy']}%",
                    inline=False
                )
            
            embed.set_footer(text="Use @bot dragon train to level up your dragon's abilities!")
            
            await message.reply(embed=embed)
            return
    except Exception as e:
        print(f"[ABILITIES MENTION] Error: {str(e)}")
    
    # Duel Command Handler - @bot duel @user
    try:
        if message.content.startswith(f"{bot.user.mention} duel"):
            args = message.content.replace(f"{bot.user.mention}", "").strip().split()
            
            if len(args) < 2:
                await message.reply("Usage: `@bot duel @user`")
                return
            
            # Get opponent from mentions
            if not message.mentions:
                await message.reply("Please mention a user to duel!")
                return
            
            opponent = message.mentions[0]
            if opponent == message.author:
                embed = discord.Embed(title="❌ Can't Duel Yourself", color=discord.Color.red())
                await message.reply(embed=embed)
                return
            
            challenger_id = message.author.id
            opponent_id = opponent.id
            guild_id = message.guild.id
            
            challenger_dragons = DragonSystem.get_dragons(challenger_id)
            opponent_dragons = DragonSystem.get_dragons(opponent_id)
            
            if not challenger_dragons:
                embed = discord.Embed(title="❌ You Have No Dragons", description="Get one with `@bot dragon hatch`!", color=discord.Color.red())
                await message.reply(embed=embed)
                return
            
            if not opponent_dragons:
                embed = discord.Embed(title="❌ Opponent Has No Dragons", description=f"{opponent.mention} doesn't have any dragons!", color=discord.Color.red())
                await message.reply(embed=embed)
                return
            
            embed = discord.Embed(
                title="⚔️ Duel Challenge Sent!",
                description=f"Waiting for {opponent.mention} to accept...\n\nYour dragon: **{challenger_dragons[0][2]}** (Lvl {challenger_dragons[0][4]})",
                color=discord.Color.gold()
            )
            await message.reply(embed=embed)
            
            # Send opponent a DM
            try:
                duel_embed = discord.Embed(
                    title="⚔️ Duel Challenge!",
                    description=f"{message.author.mention} challenged you to a dragon battle!",
                    color=discord.Color.gold()
                )
                duel_embed.add_field(name="Challenger's Dragon", value=f"**{challenger_dragons[0][2]}** (Lvl {challenger_dragons[0][4]})", inline=False)
                duel_embed.add_field(name="Your Best Dragon", value=f"**{opponent_dragons[0][2]}** (Lvl {opponent_dragons[0][4]})", inline=False)
                
                await opponent.send(embed=duel_embed)
            except:
                pass
            
            return
    except Exception as e:
        print(f"[DUEL MENTION] Error: {str(e)}")
    
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
    print(f"✅ Bot logged in as {bot.user}")
    init_database_from_seed()  # Initialize from seed if needed
    
    # Initialize dragon system tables
    if DRAGON_SYSTEM_AVAILABLE:
        try:
            DragonSystem.init_tables()
            print("✅ Dragon system tables initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize dragon tables: {e}")
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"⚠️ Command sync failed: {e}")


# -------------------------
# BACKGROUND TASKS
# -------------------------


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

@bot.tree.command(name="game-setup", description="Configure game application questions (Admin Only)")
@app_commands.describe(
    question_1="Question 1 (required)",
    question_2="Question 2 (optional)",
    question_3="Question 3 (optional)",
    question_4="Question 4 (optional)",
    question_5="Question 5 (optional)",
    target_channel="Channel to send applications to (optional - defaults to #applications)"
)
async def game_setup(
    interaction: discord.Interaction,
    question_1: str,
    question_2: Optional[str] = None,
    question_3: Optional[str] = None,
    question_4: Optional[str] = None,
    question_5: Optional[str] = None,
    target_channel: Optional[discord.TextChannel] = None
):
    """Setup game application questions for the server"""
    
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
        title="✅ Game Application Setup Complete",
        color=discord.Color.green()
    )
    embed.add_field(name="Questions Set", value=len(questions), inline=True)
    embed.add_field(name="Target Channel", value=target_channel.mention if target_channel else "Auto-detect (#applications or first channel)", inline=True)
    embed.add_field(name="Questions:", value="\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)]), inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="discord-setup", description="Configure discord application questions (Admin Only)")
@app_commands.describe(
    question_1="Question 1 (required)",
    question_2="Question 2 (optional)",
    question_3="Question 3 (optional)",
    question_4="Question 4 (optional)",
    question_5="Question 5 (optional)",
    target_channel="Channel to send applications to (optional - defaults to #applications)"
)
async def discord_setup(
    interaction: discord.Interaction,
    question_1: str,
    question_2: Optional[str] = None,
    question_3: Optional[str] = None,
    question_4: Optional[str] = None,
    question_5: Optional[str] = None,
    target_channel: Optional[discord.TextChannel] = None
):
    """Setup discord application questions for the server"""
    
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
        title="✅ Discord Application Setup Complete",
        color=discord.Color.green()
    )
    embed.add_field(name="Questions Set", value=len(questions), inline=True)
    embed.add_field(name="Target Channel", value=target_channel.mention if target_channel else "Auto-detect (#applications or first channel)", inline=True)
    embed.add_field(name="Questions:", value="\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)]), inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


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


@bot.tree.command(name="ticket", description="Get ticket creation information")
@app_commands.describe(
    action="Action to perform (info, help, create)"
)
async def ticket_info(
    interaction: discord.Interaction,
    action: str = "info"
):
    """Get information about how to create a ticket"""
    
    try:
        embed = discord.Embed(
            title="🎫 How to Create a Ticket",
            description="Go to the Important category and find 'Create a Ticket'. Click it, then create a ticket and describe what you need help with",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        print(f"[TICKET INFO] {interaction.user} requested ticket information in server {interaction.guild.name if interaction.guild else 'DM'}")
    except Exception as e:
        print(f"[TICKET INFO ERROR] {str(e)}")
        try:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        except Exception as follow_error:
            print(f"[TICKET INFO ERROR] Could not send error message: {str(follow_error)}")


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


# -------------------------
# GIVEAWAY COMMANDS
# -------------------------

@bot.tree.command(name="giveaway-setup", description="Set giveaway channel (Admin Only)")
@app_commands.describe(channel="Channel where giveaways will be posted")
async def giveaway_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set up giveaway channel"""
    
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only admins can set up giveaway channel.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        GiveawaySettingsDB.set_channel(interaction.guild.id, channel.id)
        
        embed = discord.Embed(
            title="✅ Giveaway Channel Set",
            description=f"Giveaways will be posted in {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"[GIVEAWAY] {interaction.user} set giveaway channel to {channel.name}")
    except Exception as e:
        print(f"[GIVEAWAY ERROR] {str(e)}")
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass


@bot.tree.command(name="giveaway-start", description="Start a giveaway (Admin Only)")
@app_commands.describe(
    prize="What is the prize?",
    days="How many days to run?",
    winners="How many winners?"
)
async def giveaway_start(interaction: discord.Interaction, prize: str, days: int, winners: int):
    """Start a new giveaway"""
    
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only admins can start giveaways.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get giveaway channel
        channel_id = GiveawaySettingsDB.get_channel(interaction.guild.id)
        if not channel_id:
            embed = discord.Embed(
                title="❌ Giveaway Channel Not Set",
                description="Use `/giveaway-setup` to set the giveaway channel first.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        giveaway_channel = interaction.guild.get_channel(channel_id)
        if not giveaway_channel:
            embed = discord.Embed(
                title="❌ Channel Not Found",
                description="The configured giveaway channel no longer exists.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Create giveaway
        import uuid
        giveaway_id = str(uuid.uuid4())[:8]
        end_time = datetime.utcnow() + timedelta(days=days)
        
        # Create embed for giveaway
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=prize,
            color=discord.Color.gold()
        )
        embed.add_field(name="Hosted by", value=f"<@{interaction.user.id}>", inline=False)
        embed.add_field(name="Winners", value=str(winners), inline=True)
        embed.add_field(name="Ends in", value=f"{days} day{'s' if days != 1 else ''}", inline=True)
        embed.add_field(name="Prize", value=prize, inline=False)
        embed.set_footer(text=f"React with 🎉 to enter! | ID: {giveaway_id}")
        
        # Send giveaway message
        giveaway_message = await giveaway_channel.send(embed=embed)
        await giveaway_message.add_reaction("🎉")
        
        # Save to database
        GiveawayDB.create(giveaway_id, interaction.guild.id, channel_id, giveaway_message.id, prize, days, winners, interaction.user.id, end_time)
        
        embed_confirm = discord.Embed(
            title="✅ Giveaway Started",
            description=f"Giveaway posted in {giveaway_channel.mention}\nUse `/giveaway-end` to end it early",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed_confirm, ephemeral=True)
        print(f"[GIVEAWAY] {interaction.user} started giveaway: {prize}")
    except Exception as e:
        print(f"[GIVEAWAY ERROR] {str(e)}")
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass


@bot.tree.command(name="giveaway-end", description="End a giveaway early (Admin Only)")
@app_commands.describe(giveaway_id="The giveaway ID to end")
async def giveaway_end(interaction: discord.Interaction, giveaway_id: str):
    """End a giveaway and pick winners"""
    
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only admins can end giveaways.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get giveaway
        giveaway = GiveawayDB.get(giveaway_id)
        if not giveaway:
            embed = discord.Embed(
                title="❌ Giveaway Not Found",
                description=f"No giveaway with ID: {giveaway_id}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if giveaway['ended']:
            embed = discord.Embed(
                title="❌ Already Ended",
                description="This giveaway has already been ended.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Get entries
        entries = GiveawayDB.get_entries(giveaway_id)
        
        if not entries:
            embed = discord.Embed(
                title="❌ No Entries",
                description="No one entered this giveaway.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            GiveawayDB.end_giveaway(giveaway_id)
            return
        
        # Pick winners
        num_winners = min(giveaway['winners'], len(entries))
        winners = random.sample(entries, num_winners)
        
        # Create winners embed
        winners_text = "\n".join([f"<@{winner}>" for winner in winners])
        embed = discord.Embed(
            title="🏆 GIVEAWAY ENDED 🏆",
            description=giveaway['prize'],
            color=discord.Color.gold()
        )
        embed.add_field(name="Winners", value=winners_text, inline=False)
        embed.add_field(name="Total Entries", value=str(len(entries)), inline=True)
        embed.add_field(name="Winners Count", value=str(num_winners), inline=True)
        
        # Send winners message
        channel = interaction.guild.get_channel(giveaway['channel_id'])
        if channel:
            await channel.send(embed=embed)
        
        # End giveaway
        GiveawayDB.end_giveaway(giveaway_id)
        
        embed_confirm = discord.Embed(
            title="✅ Giveaway Ended",
            description=f"Winners: {', '.join([f'<@{w}>' for w in winners])}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed_confirm, ephemeral=True)
        print(f"[GIVEAWAY] {interaction.user} ended giveaway {giveaway_id}")
    except Exception as e:
        print(f"[GIVEAWAY ERROR] {str(e)}")
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass


@bot.tree.command(name="admin-dragon-reset", description="Reset ALL users' dragon progress (Admin Only)")
@app_commands.describe(confirm="Type 'yes' to confirm - this resets EVERYONE's dragons!")
async def admin_dragon_reset(interaction: discord.Interaction, confirm: str):
    """Admin command to reset all users' dragon progress"""
    
    try:
        await interaction.response.defer(ephemeral=True)
        
        # Check admin permissions
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only server administrators can use this command.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Require confirmation
        if confirm.lower() != "yes":
            embed = discord.Embed(
                title="❌ Confirmation Required",
                description="Use `/admin-dragon-reset confirm:yes` to reset ALL users' dragons!",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Double confirmation with admin ID logging
        embed_warning = discord.Embed(
            title="⚠️ FINAL WARNING",
            description="You are about to reset **EVERYONE'S** dragons, eggs, items, and progress!\n\nThis cannot be undone!",
            color=discord.Color.red()
        )
        embed_warning.add_field(name="Admin", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
        embed_warning.add_field(name="Server", value=interaction.guild.name, inline=False)
        embed_warning.add_field(name="Action", value="MASS DRAGON RESET", inline=False)
        
        await interaction.followup.send(embed=embed_warning, ephemeral=True)
        
        # Perform the reset
        try:
            import sqlite3
            
            # Connect to database
            db_path = "bot_data.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get count of affected users before reset
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM dragons")
            affected_users = cursor.fetchone()[0]
            
            # Reset all dragons, eggs, and player data
            cursor.execute("DELETE FROM dragons")
            cursor.execute("DELETE FROM dragon_eggs")
            cursor.execute("DELETE FROM player_dragons")
            cursor.execute("DELETE FROM training_items")
            cursor.execute("DELETE FROM dragon_cooldowns")
            cursor.execute("DELETE FROM pvp_battles")
            cursor.execute("DELETE FROM duel_battles")
            
            conn.commit()
            conn.close()
            
            # Log the action
            print(f"[ADMIN DRAGON RESET] Admin {interaction.user} ({interaction.user.id}) reset all dragons!")
            print(f"[ADMIN DRAGON RESET] Affected {affected_users} users")
            
            # Confirmation embed
            embed_confirm = discord.Embed(
                title="✅ MASS RESET COMPLETE",
                description="**ALL** users' dragon progress has been reset!",
                color=discord.Color.green()
            )
            embed_confirm.add_field(name="Users Affected", value=str(affected_users), inline=True)
            embed_confirm.add_field(name="Tables Cleared", value="7 tables", inline=True)
            embed_confirm.add_field(name="Admin", value=interaction.user.mention, inline=True)
            
            await interaction.followup.send(embed=embed_confirm, ephemeral=True)
            
        except Exception as e:
            print(f"[ADMIN DRAGON RESET ERROR] {str(e)}")
            embed_error = discord.Embed(
                title="❌ Reset Failed",
                description=f"Error during reset: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed_error, ephemeral=True)
    
    except Exception as e:
        print(f"[ADMIN DRAGON RESET] Error: {str(e)}")
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass


# Handle giveaway emoji reactions
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """Handle giveaway emoji reactions"""
    
    # Ignore bot reactions
    if user.bot:
        return
    
    # Only handle 🎉 emoji
    if reaction.emoji != "🎉":
        return
    
    try:
        # Try to find giveaway by message ID
        message = reaction.message
        
        # Extract giveaway ID from embed footer
        if message.embeds and "ID:" in message.embeds[0].footer.text:
            giveaway_id = message.embeds[0].footer.text.split("ID: ")[1]
            
            giveaway = GiveawayDB.get(giveaway_id)
            if giveaway and not giveaway['ended']:
                # Add user entry
                added = GiveawayDB.add_entry(giveaway_id, user.id)
                if added:
                    print(f"[GIVEAWAY] {user} entered giveaway {giveaway_id}")
                # If already entered, just silently ignore (don't remove reaction)
    except Exception as e:
        print(f"[GIVEAWAY REACTION ERROR] {str(e)}")


@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.User):
    """Handle giveaway emoji reaction removal"""
    
    # Ignore bot reactions
    if user.bot:
        return
    
    # Only handle 🎉 emoji
    if reaction.emoji != "🎉":
        return
    
    try:
        # Try to find giveaway by message ID
        message = reaction.message
        
        # Extract giveaway ID from embed footer
        if message.embeds and "ID:" in message.embeds[0].footer.text:
            giveaway_id = message.embeds[0].footer.text.split("ID: ")[1]
            
            giveaway = GiveawayDB.get(giveaway_id)
            if giveaway and not giveaway['ended']:
                # Remove user entry
                GiveawayDB.remove_entry(giveaway_id, user.id)
                print(f"[GIVEAWAY] {user} removed from giveaway {giveaway_id}")
    except Exception as e:
        print(f"[GIVEAWAY REACTION ERROR] {str(e)}")


@bot.tree.command(name="game-application", description="Start a game application")
async def game_application(interaction: discord.Interaction):
    """Start the game application process with modals (batched 5 questions at a time)"""
    
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


@bot.tree.command(name="discord-application", description="Start a discord application")
async def discord_application(interaction: discord.Interaction):
    """Start the discord application process with modals (batched 5 questions at a time)"""
    
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
# DRAGON RIDER GAME SYSTEM
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
    
    # Start Discord bot with error handling
    try:
        print("Starting Discord bot...")
        bot.run(token)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print("❌ Discord is rate limiting this token. Please wait 30+ minutes before restarting.")
            import time
            time.sleep(60)
        raise
    except Exception as e:
        print(f"❌ Bot startup failed: {str(e)}")
        raise
