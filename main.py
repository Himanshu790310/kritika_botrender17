import os
import re
from gtts import gTTS
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import google.generativeai as genai
import nest_asyncio
import asyncio

nest_asyncio.apply()

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6138277581"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # your deployed URL

# --- Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# --- App ---
app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()

@app.on_event("startup")
async def on_startup():
    telegram_app.add_handler(CommandHandler("ask", ask))
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)

@app.post("/")
async def handle_update(request: Request):
    update_data = await request.json()
    update = Update.de_json(update_data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# --- Kritika Functions ---
def kritika_prompt(user_input: str) -> str:
    return f"""You are Kritika, a warm and patient AI English teacher for Hindi speakers...
"{user_input}"
"""

def get_kritika_reply(doubt: str) -> str:
    try:
        prompt = kritika_prompt(doubt)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Kritika abhi busy hai. Thodi der baad try karo. 🙏"

def clean_text(text): return re.sub(r"[*_~`#>\[\]()\-]", "", text)

def generate_voice(text, filename="kritika_reply.mp3"):
    gTTS(clean_text(text), lang="hi").save(filename)
    return filename

# --- /ask Command ---
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doubt = ' '.join(context.args).strip()
    name = update.effective_user.full_name
    user_id = update.effective_user.id

    if not doubt:
        await update.message.reply_text("❓ /ask ke baad apna doubt likhiye.")
        return

    await update.message.reply_text("🧠 Kritika soch rahi hai...")
    reply = get_kritika_reply(doubt)
    audio_path = generate_voice(reply)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"👩🏻‍🏫 Kritika:\n{reply}")
    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_path, "rb"))
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 From: {name} (ID: {user_id})\n❓ {doubt}\n📘 {reply}")
