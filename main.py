import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - you can change these settings
DEFAULT_DELETE_DELAY = 300  # 5 minutes in seconds
WELCOME_IMAGE_URL = "https://graph.org/file/f2265b52c6e7ac76c0b1b-31403b341de15b1ff2.jpg"  # Replace with your image URL
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7240317536:AAHttmotBWfOAFk18Q8L1q1bXJTsQ_vaPEM")  # Set this in Koyeb environment variables

# Dictionary to store group configurations: {group_id: delete_delay_in_seconds}
group_configs: Dict[int, int] = {}

# Dictionary to store message tracking: {group_id: [(message_id, timestamp, user_id)]}
message_tracking: Dict[int, List[Tuple[int, float, int]]] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    # Create inline keyboard with a customizable button
    keyboard = [
        [InlineKeyboardButton("Setup Guide", callback_data="setup_guide")],
        [InlineKeyboardButton("Visit Our Channel", url="https://t.me/filmy_men")]  # Change this URL
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = """
🤖 *Auto-Delete Bot*

This bot automatically deletes messages after a configurable time period.

*Commands:*
• /start - Show this welcome message
• /help - Display help information
• /setdelay [seconds] - Set the auto-delete delay
• /status - Check current settings

*Add me to your group and make me admin with delete messages permission!*
    """
    
    try:
        # Try to send with an image
        await update.message.reply_photo(
            photo=WELCOME_IMAGE_URL,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error sending welcome image: {e}")
        # Fallback to text only if image fails
        await update.message.reply_text(
            caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "setup_guide":
        guide_text = """
*Setup Guide:*

1. Add the bot to your group
2. Make the bot an admin with "Delete Messages" permission
3. Set your preferred auto-delete delay with /setdelay [seconds]
4. The bot will now automatically delete messages after the set time

*For more help, contact @Gojo_SatoruJi*
        """
        await query.message.reply_text(guide_text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
*Auto-Delete Bot Help*

This bot automatically deletes messages in your group after a configurable time period.

*Available Commands:*
• /start - Show the welcome message
• /help - Display this help message
• /setdelay [seconds] - Set how long messages stay before deletion
  Example: `/setdelay 300` for 5 minutes
• /status - Show current settings for this chat

*Note:* The bot needs to be an admin with the permission to delete messages.
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def set_delay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the delay for message deletion."""
    # Check if this is a group chat
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command only works in groups!")
        return
    
    # Check if the user is an admin
    user = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if user.status not in ["creator", "administrator"]:
        await update.message.reply_text("Only group administrators can use this command!")
        return
    
    # Parse the delay parameter
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Please provide a valid number of seconds.\nExample: `/setdelay 300` for 5 minutes", parse_mode=ParseMode.MARKDOWN)
        return
    
    delay = int(context.args[0])
    if delay < 10:
        await update.message.reply_text("The minimum delay is 10 seconds.")
        return
    
    # Update the configuration for this group
    group_configs[update.effective_chat.id] = delay
    
    # Confirm the change
    minutes = delay // 60
    seconds = delay % 60
    time_str = f"{minutes} minutes" if seconds == 0 else f"{minutes} minutes and {seconds} seconds"
    if minutes == 0:
        time_str = f"{seconds} seconds"
    
    await update.message.reply_text(f"✅ Messages will now be deleted after {time_str}.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the current settings for this chat."""
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command only works in groups!")
        return
    
    # Get the current delay for this group
    delay = group_configs.get(update.effective_chat.id, DEFAULT_DELETE_DELAY)
    
    # Format the time
    minutes = delay // 60
    seconds = delay % 60
    time_str = f"{minutes} minutes" if seconds == 0 else f"{minutes} minutes and {seconds} seconds"
    if minutes == 0:
        time_str = f"{seconds} seconds"
    
    # Count tracked messages
    tracked_count = len(message_tracking.get(update.effective_chat.id, []))
    
    status_text = f"""
*Current Settings:*
• Auto-delete delay: {time_str}
• Messages being tracked: {tracked_count}
• Bot version: 1.0.0

*Need help?* Use /help for commands
    """
    
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Track messages for later deletion."""
    # Ignore messages in private chats
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    
    # Don't track messages from the bot itself
    if update.effective_user.id == context.bot.id:
        return
    
    # Initialize tracking for this group if it doesn't exist
    chat_id = update.effective_chat.id
    if chat_id not in message_tracking:
        message_tracking[chat_id] = []
    
    # Add this message to tracking
    message_tracking[chat_id].append((
        update.message.message_id,
        time.time(),
        update.effective_user.id
    ))

async def cleanup_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check and delete messages that have exceeded their time limit."""
    bot = context.bot
    now = time.time()
    
    for chat_id, messages in list(message_tracking.items()):
        if not messages:
            continue
        
        # Get the delete delay for this group
        delete_delay = group_configs.get(chat_id, DEFAULT_DELETE_DELAY)
        
        # Find messages to delete
        messages_to_keep = []
        messages_to_delete = []
        
        for msg_id, timestamp, user_id in messages:
            if now - timestamp >= delete_delay:
                messages_to_delete.append(msg_id)
            else:
                messages_to_keep.append((msg_id, timestamp, user_id))
        
        # Update the tracking list
        message_tracking[chat_id] = messages_to_keep
        
        # Delete expired messages
        for msg_id in messages_to_delete:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                logger.info(f"Deleted message {msg_id} in chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to delete message {msg_id} in chat {chat_id}: {e}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setdelay", set_delay))
    application.add_handler(CommandHandler("status", status_command))
    
    # Add button callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for tracking
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add the cleanup job
    job_queue = application.job_queue
    job_queue.run_repeating(cleanup_messages, interval=10, first=10)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
