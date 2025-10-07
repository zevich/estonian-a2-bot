# app.py
import os, json
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv

from db import init_db, SessionLocal, User, Progress
from lessons import LESSONS

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret")
BASE_URL = os.getenv("BASE_URL")  # e.g. https://your-app.onrender.com

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- UI texts ---
UI = {
    "uk": {
        "welcome": "Привіт! Це естонський A2 бот. Команди: /lesson 1..7, /quiz 1..7, /progress, /setlang uk|en",
        "lesson": "Сьогоднішня тема: {topic}",
        "progress": "Прогрес: {items} запис(ів)",
        "badlang": "Використай: /setlang uk|en",
    },
    "en": {
        "welcome": "Hi! Estonian A2 bot. Commands: /lesson 1..7, /quiz 1..7, /progress, /setlang uk|en",
        "lesson": "Today's topic: {topic}",
        "progress": "Progress: {items} entries",
        "badlang": "Use: /setlang uk|en",
    }
}

# --- helpers ---
def get_lang(chat_id):
    s = SessionLocal()
    u = s.query(User).filter_by(chat_id=str(chat_id)).first()
    s.close()
    return u.lang if u else "uk"

# --- command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    s = SessionLocal()
    u = s.query(User).filter_by(chat_id=str(chat_id)).first()
    if not u:
        u = User(chat_id=str(chat_id), level="A2", lang="uk")
        s.add(u)
        s.commit()
    s.close()
    lang = get_lang(chat_id)
    await update.message.reply_text(UI[lang]["welcome"])

async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args or context.args[0] not in ("uk", "en"):
        await update.message.reply_text(UI["uk"]["badlang"])
        return
    s = SessionLocal()
    u = s.query(User).filter_by(chat_id=str(chat_id)).first()
    if u:
        u.lang = context.args[0]
        s.commit()
    s.close()
    await update.message.reply_text(f"OK, lang = {context.args[0]}")

async def lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = get_lang(chat_id)
    day = int(context.args[0]) if context.args else 1
    day = max(1, min(7, day))
    data = LESSONS[day]
    vocab_lines = "\n".join([f"• {et} → {ua} → {en}" for et, ua, en in data["vocab"]])
    text = (
        UI[lang]["lesson"].format(topic=data["topic"])
        + f"\n\nSõnastik:\n{vocab_lines}\n\nHarjutus:\n- "
        + "\n- ".join(data["exercise"])
        + "\n\n/quiz "
        + str(day)
    )
    await update.message.reply_text(text)

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = int(context.args[0]) if context.args else 1
    _ = LESSONS.get(day, LESSONS[1])
    q = [
        "Täida: Ma ostan ___ (õun).",
        "Tõlgi: Де вокзал?",
        "Vali: meeldib + ? (partitiiv)",
    ]
    kb = [[InlineKeyboardButton("Näita vastuseid", callback_data=f"ans:{day}")]]
    await update.message.reply_text("\n".join(q), reply_markup=InlineKeyboardMarkup(kb))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("ans:"):
        day = int(query.data.split(":")[1])
        answers = ["õuna", "Kus on jaam?", "meeldib + partitiiv"]
        # store progress
        s = SessionLocal()
        s.add(Progress(chat_id=str(query.message.chat.id), day=day, result=json.dumps({"answers": answers})))
        s.commit()
        s.close()
        await query.edit_message_text("Vastused:\n- " + "\n- ".join(answers))

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    s = SessionLocal()
    count = s.query(Progress).filter_by(chat_id=str(chat_id)).count()
    s.close()
    lang = get_lang(chat_id)
    await update.message.reply_text(UI[lang]["progress"].format(items=count))

# register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("setlang", setlang))
application.add_handler(CommandHandler("lesson", lesson))
application.add_handler(CommandHandler("quiz", quiz))
application.add_handler(CommandHandler("progress", progress))
application.add_handler(CallbackQueryHandler(button))

# --- Flask webhook endpoints ---
@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

@app.route("/")
def index():
    return "OK"

if __name__ == "__main__":
    init_db()
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        url_path=WEBHOOK_SECRET,
        webhook_url=f"{BASE_URL}/{WEBHOOK_SECRET}" if BASE_URL else None
    )
