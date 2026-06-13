# Bot Database Backup System

Your Discord bot settings are now automatically persisted across code updates!

## How It Works

The bot uses two database files:

1. **`bot_data.db`** - Your active database (gitignored)
   - Created and updated when the bot runs
   - Contains all current settings
   - NOT committed to git (to avoid merge conflicts)

2. **`bot_data_seed.db`** - Your configuration seed (committed to git)
   - Snapshot of your settings
   - Used to initialize fresh deployments
   - Committed to git so settings survive code updates

## Before Deploying or Pushing Code

**Always backup your database to preserve settings:**

```bash
python backup_db.py
```

This will:
- Copy `bot_data.db` → `bot_data_seed.db`
- Create a timestamped backup of the old seed
- Show you the next git steps

## Git Workflow

```bash
# 1. Make your code changes and test them locally
# 2. Update your bot configuration in Discord
# 3. Backup the database
python backup_db.py

# 4. Commit and push
git add bot_data_seed.db
git commit -m "Update bot settings and configuration"
git push
```

## Deployment

When you deploy to a new machine:

1. Pull the code: `git pull`
2. Start the bot
3. The bot will automatically:
   - Check if `bot_data.db` exists
   - If not, copy `bot_data_seed.db` → `bot_data.db`
   - Load all your saved settings
   - You're ready to go! ✅

## Files in .gitignore

```
bot_data.db              # Active database (not tracked)
*.db.backup_*            # Timestamped backups (not tracked)
.env                     # Environment variables
```

## What Gets Saved?

All your Discord bot configuration:
- ✅ Application questions (game & discord)
- ✅ Realm code channel
- ✅ Giveaway settings
- ✅ User cooldowns
- ✅ Active applications
- ✅ All other server settings

## Troubleshooting

**Settings lost after pulling?**
- You forgot to run `python backup_db.py` before pushing
- Solution: Reconfigure, run backup, and push again

**Want to reset to a previous backup?**
```bash
cp bot_data_seed.db.backup_YYYYMMDD_HHMMSS bot_data_seed.db
python backup_db.py  # Confirm and commit
```

**Want to start fresh?**
```bash
rm bot_data.db
# Bot will create a new one on next run
```
