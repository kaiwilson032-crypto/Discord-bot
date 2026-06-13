# Firebase Setup Guide for Discord Bot

Your bot now uses **Firebase/Firestore** to save all settings (realm codes, application questions, etc.) so they persist permanently!

## Step 1: Create a Firebase Project

1. Go to https://console.firebase.google.com/
2. Click **"Create a project"**
3. Name it (e.g., "Discord Bot")
4. Enable Google Analytics (optional)
5. Click **Create Project** and wait

## Step 2: Create a Firestore Database

1. In your Firebase project, go to **Firestore Database** (left sidebar)
2. Click **Create database**
3. Start in **Production mode**
4. Choose your location (closest to your server)
5. Click **Create**

## Step 3: Generate Service Account Key

1. Go to **Project Settings** (gear icon, top right)
2. Click **Service Accounts** tab
3. Click **Generate new private key** button
4. A JSON file will download - **SAVE THIS SAFELY**

## Step 4: Add to Your .env File

1. Open the JSON file you downloaded
2. Copy the ENTIRE JSON content
3. In your `.env` file, add:

```
FIREBASE_CREDENTIALS={"type":"service_account","project_id":"your-project-id",...}
```

**Paste the entire JSON as one line**

Example:
```
FIREBASE_CREDENTIALS={"type":"service_account","project_id":"discord-bot-abc123","private_key_id":"key123","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE...","client_email":"firebase-adminsdk-abc@discord-bot-abc123.iam.gserviceaccount.com",...}
```

## Step 5: Install Firebase SDK

On Railway or your machine, run:
```
pip install firebase-admin
```

Or add to `requirements.txt`:
```
firebase-admin==6.0.0
```

## Step 6: Test It!

1. Update your bot code with the new version I provided
2. Commit and push to git
3. Deploy on Railway
4. Set a realm code or application questions in Discord
5. Redeploy or stop/start the bot
6. Check if settings persisted ✅

## How It Works

- **First time**: Bot uses Firebase if credentials found, otherwise falls back to SQLite
- **Logging**: Console shows `[FIREBASE] ✅` when saving to Firebase or `[SQLITE]` for fallback
- **No data loss**: Even if bot crashes, settings are saved in Firebase cloud
- **Backup**: Your settings are automatically backed up by Firebase

## Troubleshooting

**"FIREBASE_CREDENTIALS not in .env"**
- Add the JSON to your `.env` file as shown above

**Settings not saving**
- Check Railway logs for `[FIREBASE]` messages
- If you see `[SQLITE]`, Firebase isn't initialized - check credentials

**Need to reset Firebase?**
1. Go to Firestore Console
2. Delete the collections
3. Bot will recreate them fresh

## Optional: Monitor Your Data

View your saved settings in Firebase:
1. Go to your Firebase project
2. Firestore Database
3. Look at collections: `realm_codes`, `server_settings`
4. You can manually edit/delete data here

That's it! Your settings are now cloud-backed! ☁️
