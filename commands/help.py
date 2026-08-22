from telegram import Update, constants
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import nest_asyncio
import requests

# imported escape_html func from formatting.pyyyy
from utils.formatting import escape_html

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 <b>Available Commands</b>:
/chat - Activate bot in this group
/stop - Deactivate bot
/ask <query> - Ask something with AI
/reset - Reset your chat history
/help - Show this help message
    """
    # Apply HTML escape to ensure proper formatting
    await update.message.reply_text(escape_html(help_text), parse_mode="HTML")