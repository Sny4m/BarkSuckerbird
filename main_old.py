from flask import Flask
from threading import Thread
import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram import constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from duckduckgo_search import DDGS as ddg
import requests
import re
import json

groq_api = os.environ['GROQ']
temp = 'key'


app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

user_histories = {}
active_chats = set()

BOT = os.environ['BOT']
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ['API_KEY_BA']
)

# Function to escape special characters for HTML formatting
def escape_html(text):
    # List of characters to escape for HTML formatting
    html_escape_map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
        "/": "&#47;"
    }
    return ''.join(html_escape_map.get(c, c) for c in text)

# Commands
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

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = ' '.join(context.args)
    if not user_input:
        await update.message.reply_text("<b>❗ Please ask something after /ask.</b>", parse_mode="HTML")
        return

    messages = [{"role": "system", "content": os.environ['CONTEXT_AI']}, {"role": "user", "content": user_input}]
    response = client.chat.completions.create(model=os.environ['MODEL'], messages=messages, max_tokens=800)
    reply = response.choices[0].message.content.strip()
    await update.message.reply_text(escape_html(reply), parse_mode="HTML", reply_to_message_id=update.message.message_id)

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

def get_ai_reply(user_id, input_text):
    user_id = str(user_id)
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": input_text})
    messages = [{"role": "system", "content": os.environ['CONTEXT_AI']}] + history
    response = client.chat.completions.create(model=os.environ['MODEL'], messages=messages, max_tokens=800)
    reply = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": reply})
    user_histories[user_id] = history[-50:]
    return reply

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    count = len(user_histories.get(user_id, []))
    user_histories.pop(user_id, None)
    await update.message.reply_text(f"<b>✅ Conversation reset! {count} messages cleared.</b>", parse_mode="HTML")




async def web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = ' '.join(context.args)
    res = ddgSearch(user_input)
    reply = groq(res, user_input)
    await update.message.reply_text(reply)


def ddgSearch(chat):
    with ddg() as ddgs:
        results = ddgs.text(chat, max_results=5)
        results = f'{results}'
        return results
        



def groq(data, user_input):
    headers = {
        "Authorization": f"Bearer {groq_api}",
        "Content-Type": "application/json"
    }
    context = '''
You are an intelligent answer extractor
You will be given a list of search results from DuckDuckGo in the form of dictionaries with keys title href and body

Your task is to read all the results understand them and return a clear direct answer to the users query

Your response must follow these rules

1 Return only the answer no introductions no phrases like The answer is According to sources etc
2 If the query is a yes or no question always start your response with a clear Yes or No followed by a short explanation or key data if needed
For example
Q Are CBSE 10th results out
A Yes the CBSE Class 10 results are out The overall pass percentage is 93.66 percent
3 If the query is factual or definitional return only the most accurate and concise answer
For example
Q Capital of France
A Paris
4 If context is needed keep it brief and directly connected to the answer
For example
Q Who founded Microsoft
A Microsoft was founded by Bill Gates and Paul Allen in 1975
5 If information is missing ambiguous or conflicting say so briefly
For example
A The available results are unclear or contradictory about this topic
6 Ignore unrelated content ads forum spam SEO junk and repeated info

Return your final answer in a small paragraph no markdown no bullet points no citations


'''
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": f"{context}"},
            {"role": "user", "content": f"Question: {user_input}\nSearch Results:\n{data}"}
        ],
        "max_tokens": 500
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"]

# ----------------- texting ------------------
USERS_FILE = "userss.json"

OWNER_USERNAME = "arushbaluni"
authorized_users = {OWNER_USERNAME}


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        # Return empty structure if file missing
        return {"users": {}, "groups": {}}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def txt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.username not in authorized_users:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    text = update.message.text
    pattern = r"````(.*?)````"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        await update.message.reply_text("❌ Message must be enclosed in ````backticks````.")
        return

    msg_to_send = match.group(1).strip()
    remaining = re.sub(pattern, "", text).replace("/txt", "").strip()
    recipients = remaining.split()

    if not recipients:
        await update.message.reply_text("❌ Please specify at least one user ID or username.")
        return

    data = load_users()
    users = data.get("users", {})
    groups = data.get("groups", {})

    # Update users file with sender info if not present
    sender_username = user.username
    sender_id = user.id
    if sender_username and sender_username not in users:
        users[sender_username] = sender_id
        data["users"] = users
        save_users(data)

    success = []
    failed = []

    for recipient in recipients:
        recipient_clean = recipient.lstrip("@")

        if recipient_clean in users:
            chat_id = users[recipient_clean]
        elif recipient_clean in groups:
            chat_id = groups[recipient_clean]
        else:
            if recipient_clean.isdigit():
                chat_id = int(recipient_clean)
            else:
                failed.append(f"{recipient} (username/group not found in userss.json)")
                continue

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=msg_to_send,
                parse_mode=constants.ParseMode.HTML
            )
            success.append(recipient)
        except Exception as e:
            failed.append(f"{recipient} ({e})")

    report = f"✅ Sent to: {', '.join(success)}\n"
    if failed:
        report += "❌ Failed to send to:\n" + "\n".join(failed)

    await update.message.reply_text(report)


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != OWNER_USERNAME:
        await update.message.reply_text("❌ Only the owner can authorize users.")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /auth <username>")
        return

    username = context.args[0].lstrip("@")
    if username in authorized_users:
        await update.message.reply_text(f"ℹ️ @{username} is already authorized.")
    else:
        authorized_users.add(username)
        await update.message.reply_text(f"✅ Authorized @{username} to use /txt.")


async def revoke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != OWNER_USERNAME:
        await update.message.reply_text("❌ Only the owner can revoke users.")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /revoke <username>")
        return

    username = context.args[0].lstrip("@")
    if username not in authorized_users:
        await update.message.reply_text(f"ℹ️ @{username} is not authorized.")
    else:
        authorized_users.remove(username)
        await update.message.reply_text(f"✅ Revoked @{username} from /txt access.")









# Main
async def main():
    app = ApplicationBuilder().token(BOT).build()
    app.add_handler(CommandHandler("chat", chat_command))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
    app.add_handler(CommandHandler("web", web))    
    app.add_handler(CommandHandler("txt", txt_command))
    app.add_handler(CommandHandler("auth", auth_command))
    app.add_handler(CommandHandler("revoke", revoke_command))
    print("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    keep_alive()
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
