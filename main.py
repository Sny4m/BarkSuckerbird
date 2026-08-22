import os
from flask import Flask
from threading import Thread
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from commands.cbot import chat_command, stop, reset
from commands.help import help_command
from commands.web import web
from core.ai import ai_reply

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

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

    # Only registers non command txts
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))

    print("🤖 Bot is starting up and polling for messages...")
    
    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main()