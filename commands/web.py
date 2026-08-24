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
from ddgs.exceptions import DDGSException
# imported dggSearch from /source/dgg.py (search.dgg hai)
from search.ddg import ddgSearch
from search.ddg import groq
import asyncio

# Used asyncio because groq is taking some time to respond!!!!!!!!!!!!

async def web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = ' '.join(context.args)
    if not user_input:
        await update.message.reply_text("❌ Usage: /web <your search query>")
        return

    try:
        res = await asyncio.to_thread(ddgSearch, user_input)
        reply = await asyncio.to_thread(groq, res, user_input)
    except DDGSException:
        await update.message.reply_text("❌ DuckDuckGo search failed, try again in a bit.")
        return
    except requests.RequestException:
        await update.message.reply_text("❌ The AI service didn't respond, try again in a bit.")
        return
    except (KeyError, IndexError):
        await update.message.reply_text("❌ Got a weird response back, try again.")
        return

    await update.message.reply_text(reply)