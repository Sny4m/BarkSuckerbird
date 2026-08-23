import asyncio
import logging
import os

from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from core.database import active_chats, user_histories
from utils.formatting import escape_html

logger = logging.getLogger(__name__)

OPENROUTER_MODEL = os.environ.get('MODEL')
OPENROUTER_KEY = os.environ.get('OPENROUTER')

if not OPENROUTER_KEY:
    logger.error("OPENROUTER env var is not set - AI chat will fail on every message.")
if not OPENROUTER_MODEL:
    logger.error("MODEL env var is not set - AI chat will fail on every message.")
if not os.environ.get('CONTEXT_AI'):
    logger.warning("CONTEXT_AI env var is not set - AI will run with no system prompt.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key= OPENROUTER_KEY,
)


def get_ai_reply(user_id, input_text):
    user_id = str(user_id)
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": input_text})
    messages = [{"role": "system", "content": os.environ.get('CONTEXT_AI')}] + history
    response = client.chat.completions.create(
        model= OPENROUTER_MODEL,
        messages=messages,
        max_tokens=800,
    )
    reply = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": reply})
    user_histories[user_id] = history[-50:]
    return reply


async def _keep_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    # Telegram's typing indicator only lasts ~5s, so keep refreshing it
    # while the AI request is in flight.
    try:
        while True:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass


async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"] and chat.id not in active_chats:
        return

    user_input = update.message.text
    user_id = update.effective_user.id
    ai_input = logic(user_input)

    typing_task = asyncio.create_task(_keep_typing(context, chat.id))
    try:
        response = await asyncio.to_thread(get_ai_reply, user_id, ai_input)
    except Exception:
        logger.exception("AI reply failed for user %s", user_id)
        typing_task.cancel()
        await update.message.reply_text(
            "<b>⚠️ AI is having trouble responding right now, try again in a bit.</b>",
            parse_mode="HTML",
        )
        return
    finally:
        typing_task.cancel()

    await update.message.reply_text(escape_html(response), parse_mode="HTML", reply_to_message_id=update.message.message_id)


def logic(input: str):
    return input.replace('/pyai', '').replace('pyai', '').strip()
