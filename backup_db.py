#!/usr/bin/env python3
"""
Backup bot database to seed file before committing to git.
Run this script before pushing to git to persist your Discord bot settings.

Usage: python backup_db.py
"""

import shutil
import os
from datetime import datetime

DB_PATH = "bot_data.db"
SEED_DB_PATH = "bot_data_seed.db"

def backup_database():
    """Backup the current bot database to seed file"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: {DB_PATH} not found!")
        print("   Make sure the bot has run at least once to create the database.")
        return False
    
    try:
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{SEED_DB_PATH}.backup_{timestamp}"
        
        # If seed exists, backup the old one first
        if os.path.exists(SEED_DB_PATH):
            shutil.copy(SEED_DB_PATH, backup_path)
            print(f"📦 Backed up old seed to: {backup_path}")
        
        # Copy current database to seed
        shutil.copy(DB_PATH, SEED_DB_PATH)
        print(f"✅ Database backed up successfully!")
        print(f"   {DB_PATH} → {SEED_DB_PATH}")
        print(f"\n📝 Next steps:")
        print(f"   1. git add bot_data_seed.db")
        print(f"   2. git commit -m 'Update bot configuration'")
        print(f"   3. git push")
        print(f"\n💡 This will preserve all your Discord settings when deploying!")
        return True
        
    except Exception as e:
        print(f"❌ Error backing up database: {str(e)}")
        return False

if __name__ == "__main__":
    backup_database()
