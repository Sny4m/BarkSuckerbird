# CBOT == Chat Bot commands 
# Includes /start / stop /reset and the wake(/pyai) command

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
from core.database import user_histories, active_chats
from utils.formatting import escape_html


async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        active_chats.add(chat.id)
        await update.message.reply_text("<b>✅ Bot activated in this group.</b>", parse_mode="HTML")
    else:
        welcome_text = escape_html("""
👋 <b>Hey there!</b> I'm your friendly AI assistant powered by <b>Multiple Free AI Models</b> 🧠⚡️

💬 Just send me any question or message, and I’ll respond using the best available AI model!

🔍 <b>Examples</b>:
• What's the capital of Norway?
• Summarize a paragraph
• Help me write a poem
• Debug my Python code

✨ <b>Type anything to get started!</b>
""")
        await update.message.reply_text(welcome_text, parse_mode="HTML")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        if chat.id in active_chats:
            active_chats.remove(chat.id)
            await update.message.reply_text("<b>🛑 Bot deactivated in this group.</b>", parse_mode="HTML")
        else:
            await update.message.reply_text("<b>❗️Bot is already inactive here.</b>", parse_mode="HTML")
    else:
        await update.message.reply_text("<b>🚫 This command is for group chats only.</b>", parse_mode="HTML")


# RESET COMMAND (IT LOOKS GOOD HERE could move it to database.py ig?)
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    count = len(user_histories.get(user_id, []))
    user_histories.pop(user_id, None)
    await update.message.reply_text(f"<b>✅ Conversation reset! {count} messages cleared.</b>", parse_mode="HTML")
