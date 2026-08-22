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
# imported dggSearch from /source/dgg.py (search.dgg hai)
from search.ddg import ddgSearch
from search.ddg import groq

async def web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = ' '.join(context.args)
    res = ddgSearch(user_input)
    reply = groq(res, user_input)
    await update.message.reply_text(reply)