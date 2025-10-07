# Estonian A2 Tutor Bot

Telegram bot for A2 Estonian practice (UA/EN UI). Stores progress in DB.

## Commands
/start – welcome & profile
/setlang uk|en – switch UI
/lesson 1..7 – show topic, vocab, exercises
/quiz 1..7 – mini-quiz with answers button
/progress – progress entries count

## Deploy (Render)
1) Create bot with @BotFather → copy TELEGRAM_TOKEN
2) Deploy this repo to Render → Web Service
   - Build: `pip install -r requirements.txt`
   - Start: `python app.py`
3) Add Environment variables:
   - TELEGRAM_TOKEN = <your token>
   - WEBHOOK_SECRET = <random-long-string>
   - BASE_URL = https://<your-service>.onrender.com
4) Manual Redeploy
5) Open Telegram → /start → /lesson 1

## Database
Default: SQLite (ephemeral on Render). For persistence:
- Create Render PostgreSQL, get External Database URL
- Add env var: DATABASE_URL=<postgres url>
- Redeploy

## Local run (testing)
- Create `.env` with TELEGRAM_TOKEN, WEBHOOK_SECRET, BASE_URL (use ngrok if needed)
- `pip install -r requirements.txt`
- `python app.py`
