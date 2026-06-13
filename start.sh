#!/bin/bash

# Discord Bot Startup Script with Automatic Database Backup
# This script backs up your bot settings, then starts the bot

echo "🤖 Discord Bot Startup"
echo "===================="

# Step 1: Navigate to app directory
cd /app

# Step 2: Backup the database
echo ""
echo "📦 Backing up bot settings..."
python backup_db.py

if [ $? -eq 0 ]; then
    echo "✅ Backup successful!"
else
    echo "⚠️  Backup failed (this is OK if it's first run)"
fi

# Step 3: Start the bot
echo ""
echo "🚀 Starting bot..."
python bot.py
