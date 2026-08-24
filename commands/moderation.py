import json
import os
import re
import logging

from telegram import Update, constants
from telegram.error import TelegramError
from telegram.ext import ContextTypes

USERS_FILE = "userss.json"
OWNER_USERNAME = "arushbaluni"
authorized_users = {OWNER_USERNAME}


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
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
    pattern = r'"(.*?)"'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        await update.message.reply_text('❌ Usage: /txt <user_or_group> "your message"')
        return

    msg_to_send = match.group(1).strip()
    if not msg_to_send:
        await update.message.reply_text("❌ Message can't be empty.")
        return

    recipients = re.sub(pattern, "", text).replace("/txt", "").strip().split()
    if not recipients:
        await update.message.reply_text("❌ Please specify at least one user ID or username.")
        return

    data = load_users()
    users = data.get("users", {})
    groups = data.get("groups", {})

    # Update users file with sender info if not present
    sender_username = user.username
    if sender_username and sender_username not in users:
        users[sender_username] = user.id
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
        elif recipient_clean.isdigit():
            chat_id = int(recipient_clean)
        else:
            failed.append(f"{recipient} (username/group not found in {USERS_FILE})")
            continue

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=msg_to_send,
                parse_mode=constants.ParseMode.HTML
            )
            success.append(recipient if recipient.startswith("@") else f"@{recipient}")
        except TelegramError as e:
            failed.append(f"{recipient} ({e})")

    report = f"✅ Message sent successfully to: {', '.join(success) if success else 'no recipients'}\n"
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


# Enable logging to see background information in the console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def log_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function triggers whenever the bot receives a message in a group."""
    message = update.message
    user = message.from_user
    chat = message.chat

    print("\n--- NEW MESSAGE RECEIVED ---")
    print(f"Group/Chat Name: {chat.title} (ID: {chat.id})")
    print(f"Sender Name:    {user.full_name}")
    print(f"Sender User ID: {user.id}")  # <-- This is the User ID you are looking for
    print(f"Message Text:   '{message.text}'")
    print("----------------------------\n")



