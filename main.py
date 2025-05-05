import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# ========================
# CONFIGURATION
# ========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DELETE_AFTER_SECONDS = int(os.environ.get("DELETE_AFTER", 300))

START_PHOTO_URL = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"
START_QUOTE = "🌟 *“The best way to predict the future is to create it.”*"
BUTTON_TEXT = "🔗 Visit Source"
BUTTON_URL = "https://example.com"

# ========================
# FLASK APP
# ========================

app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Bot is running on Koyeb!"

# ========================
# TELEGRAM BOT SETUP
# ========================

telegram_app = Application.builder().token(BOT_TOKEN).build()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(BUTTON_TEXT, url=BUTTON_URL)]
    ])
    await update.message.reply_photo(
        photo=START_PHOTO_URL,
        caption=START_QUOTE,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# Message auto-delete handler
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.chat.type in ['group', 'supergroup'] and not msg.from_user.is_bot:
        await asyncio.sleep(DELETE_AFTER_SECONDS)
        try:
            await msg.delete()
        except Exception as e:
            print(f"❌ Could not delete message: {e}")

# Telegram webhook endpoint
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"

# Register handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_after_delay))
