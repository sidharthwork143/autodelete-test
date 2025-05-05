from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
import asyncio

TOKEN = os.environ.get("7625916423:AAEKuSbQoBZQc55Qa0jvsqgK8t4dAJqk7Rs")  # Set this in Koyeb environment variables
DELETE_DELAY_SECONDS = 300  # 5 minutes. Change to desired seconds

START_IMAGE_URL = "https://yourdomain.com/your-image.jpg"  # Replace with your image URL
START_CAPTION = "🤖 This bot deletes user messages after a set time.\n\n🛠 Features:\n- Auto delete\n- Custom caption\n- Inline button"

INLINE_BUTTON_TEXT = "View Source"
INLINE_BUTTON_URL = "https://github.com/your-bot-link"

# Flask setup
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Telegram bot setup
bot_app = Application.builder().token(TOKEN).build()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(INLINE_BUTTON_TEXT, url=INLINE_BUTTON_URL)]])
    await update.message.reply_photo(
        photo=START_IMAGE_URL,
        caption=START_CAPTION,
        reply_markup=keyboard
    )

# Message handler to auto-delete
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup']:
        msg = update.message
        await asyncio.sleep(DELETE_DELAY_SECONDS)
        try:
            await context.bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
        except Exception as e:
            print(f"Failed to delete message: {e}")

# Telegram webhook handler
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put_nowait(update)
    return "ok"

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_group_message))
