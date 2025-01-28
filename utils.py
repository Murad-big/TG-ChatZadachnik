import hashlib
from config import ALLOWED_CHAT_ID, ALLOWED_USERNAMES
from telegram import Update
from telegram.ext import ContextTypes

def generate_task_hash(username, task, deadline):
    hash_input = f"{username}-{task}-{deadline}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:8]

def is_editor(update: Update) -> bool:
    username = update.effective_user.username
    return username in ALLOWED_USERNAMES

def restricted_edit(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_editor(update):
            if update.message:
                await update.message.reply_text("У вас нет прав для редактирования.")
            elif update.callback_query:
                await update.callback_query.answer("У вас нет прав для редактирования.", show_alert=True)
            return
        await handler(update, context)
    return wrapper

def is_valid_chat(update: Update) -> bool:
    chat_id = update.effective_chat.id
    return chat_id == ALLOWED_CHAT_ID

def restricted(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_valid_chat(update):
            return
        await handler(update, context)
    return wrapper
