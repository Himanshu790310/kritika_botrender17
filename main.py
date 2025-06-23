import os
import re
import asyncio
from gtts import gTTS
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import google.generativeai as genai

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Prompt template
def kritika_prompt(user_input: str) -> str:
    return f"""
You are Kritika, a warm, polite AI English teacher for Hindi-speaking students.
Your role:
- Reply in Hinglish (90% Hindi + 10% English) if asked in Hindi
- Reply in English if asked in English
- Use grammar formulas, examples, and cultural context
Avoid political/romantic/religious content.

Student asked: "{user_input}"

End with: "Aur koi doubt hai?" or "Main aur madad kar sakti hoon?"
"""

# Generate Gemini reply
def get_kritika_reply(doubt: str) -> str:
    try:
        prompt = kritika_prompt(doubt)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Kritika abhi thoda busy hai. Thodi der baad try kariye. 🙏"

# Generate voice
def clean_text(text):
    return re.sub(r"[*_~`#>\\[\\]()\\-]", "", text)

def generate_voice(text, filename="kritika_reply.mp3"):
    cleaned_text = clean_text(text)
    tts = gTTS(cleaned_text, lang="hi")
    tts.save(filename)
    return filename

# Telegram command
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doubt = ' '.join(context.args).strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name

    if not doubt:
        await update.message.reply_text("❓ /ask ke baad apna doubt likhiye. Jaise: /ask noun ke types kya hote hain")
        return

    await update.message.reply_text("🧠 Kritika soch rahi hai...")

    reply = get_kritika_reply(doubt)
    audio_path = generate_voice(reply)

    await update.message.reply_text(f"👩🏻‍🏫 Kritika:\n{reply}")
    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_path, "rb"))

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Doubt by {user_name} (ID: {user_id}):\n{doubt}\n\n📘 Reply:\n{reply}"
    )

# Bot launcher
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("ask", ask))
    print("✅ Kritika is live via polling on GCP.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
