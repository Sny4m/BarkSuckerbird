import logging
import os
from threading import Thread

from dotenv import load_dotenv
from flask import Flask
from telegram.error import Conflict
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

load_dotenv()

from commands.cbot import chat_command, reset, stop
from commands.help import help_command
from commands.moderation import auth_command, revoke_command, txt_command
from commands.web import web
from core.ai import ai_reply

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

async def error_handler(update, context):
    if isinstance(context.error, Conflict):
        logger.warning("Another bot instance is already polling with this token - stop that one first.")
        return
    logger.error("Unhandled exception while processing an update", exc_info=context.error)

def main():
    token = os.environ.get("BOT")
    if not token:
        raise ValueError("No BOT token found in environment variables!")

    # Build the application
    app = ApplicationBuilder().token(token).build()

    # Register command handlers
    app.add_handler(CommandHandler("chat", chat_command))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("web", web))
    app.add_handler(CommandHandler("txt", txt_command))
    app.add_handler(CommandHandler("auth", auth_command))
    app.add_handler(CommandHandler("revoke", revoke_command))

    # Only registers non command txts
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))

    app.add_error_handler(error_handler)

    keep_alive()

    print("🤖 Bot is starting up and polling for messages...")

    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main()