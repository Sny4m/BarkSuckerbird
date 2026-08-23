import os

import nest_asyncio
import requests
from openai import OpenAI
from telegram import Update, constants
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.database import active_chats, user_histories
from utils.formatting import escape_html

BOT = os.environ.get('BOT')
OPENROUTER_MODEL = os.environ.get('MODEL')

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get('API_KEY_BA')
)


def get_ai_reply(user_id, input_text):
    user_id = str(user_id)
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": input_text})
    messages = [{"role": "system", "content": os.environ.get('CONTEXT_AI')}] + history
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=messages,
        max_tokens=800,
    )
    reply = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": reply})
    user_histories[user_id] = history[-50:]
    return reply



async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"] and chat.id not in active_chats:
        return

    user_input = update.message.text
    user_id = update.effective_user.id
    ai_input = logic(user_input)
    response = get_ai_reply(user_id, ai_input)
    await update.message.reply_text(escape_html(response), parse_mode="HTML", reply_to_message_id=update.message.message_id)

def logic(input: str):
    return input.replace('/pyai', '').replace('pyai', '').strip()