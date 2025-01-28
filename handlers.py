from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from excel_manager import read_excel_data, add_task_to_excel, write_excel_data
from utils import generate_task_hash, restricted, restricted_edit
from datetime import datetime
import re
from telegram.ext import (
    ContextTypes,
)


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Привет, я Бот для постановки задач")
    else:
        print("update.message is None")

@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Я могу выполнять следующие команды:\n"
        "/start - проверить, что бот работает\n"
        "/help - узнать список доступных команд\n"
        "/set_deadline @username DD/MM/YYYY описание задачи - назначить задачу\n"
        "/check_deadline - просмотреть задачи\n"
    )
    await update.message.reply_text(help_text)

@restricted
async def check_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        names, _, _, _ = read_excel_data()
        unique_names = sorted(set(names))


        keyboard = [[InlineKeyboardButton(name, callback_data=f"user:{name}")] for name in unique_names]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Выберите пользователя:", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

@restricted_edit
async def task_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_hash = query.data.split(":")[1]
    names, desc, dates, statuses = read_excel_data()

    selected_task = None
    task_date = None
    task_status = None

    for i in range(len(desc)):
        task_hash = generate_task_hash(names[i], desc[i], dates[i])
        if task_hash == selected_hash:
            selected_task = desc[i]
            task_date = dates[i]
            task_status = statuses[i]
            break

    if not selected_task:
        await query.edit_message_text("Задача не найдена.")
        return

    task_status_icon = "✅" if task_status == "Done" else "❌"

    keyboard = [
        [
            InlineKeyboardButton("Не сделано ❌", callback_data=f"status:undone:{selected_hash}"),
            InlineKeyboardButton("Сделано ✅", callback_data=f"status:done:{selected_hash}"),
        ],
        [
            InlineKeyboardButton("Удалить 🗑", callback_data=f"delete:{selected_hash}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Задача: {selected_task}\n"
        f"Дедлайн: {task_date}\n"
        f"Статус: {task_status_icon}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup
    )

@restricted_edit
async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, selected_hash = query.data.split(":")
    names, desc, dates, statuses = read_excel_data()

    for i in range(len(desc)):
        task_hash = generate_task_hash(names[i], desc[i], dates[i])
        if task_hash == selected_hash:
            del names[i]
            del desc[i]
            del dates[i]
            del statuses[i]
            write_excel_data(names, desc, dates, statuses)
            break

    await query.edit_message_text("Задача удалена.")


async def user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_user = query.data.split(":")[1]
    names, desc, dates, _ = read_excel_data()

    user_tasks = [
        {"desc": desc[i], "date": dates[i], "hash": generate_task_hash(names[i], desc[i], dates[i])}
        for i in range(len(names)) if names[i] == selected_user
    ]

    if not user_tasks:
        await query.edit_message_text(f"У {selected_user} нет задач.")
        return

    keyboard = [
        [InlineKeyboardButton(task["desc"][:21] + "...", callback_data=f"task:{task['hash']}")]
        for task in user_tasks
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Задачи для {selected_user}:", reply_markup=reply_markup)

@restricted_edit
async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, status, selected_hash = query.data.split(":")
    names, desc, dates, statuses = read_excel_data()

    for i in range(len(desc)):
        task_hash = generate_task_hash(names[i], desc[i], dates[i])
        if task_hash == selected_hash:
            statuses[i] = "Done" if status == "done" else "Undone"
            write_excel_data(names, desc, dates, statuses)
            break

    new_status_icon = "✅" if status == "done" else "❌"
    await query.edit_message_text(
        f"Статус задачи обновлен на {new_status_icon}.",
    )

@restricted
@restricted_edit
async def set_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            if update.callback_query:
                await update.callback_query.answer("Эта команда должна быть вызвана из текстового сообщения.", show_alert=True)
            return

        text = update.message.text.strip()

        if not text.startswith("/set_deadline "):
            await update.message.reply_text("Неверный формат команды.")
            return

        text = text[len("/set_deadline "):].strip()

        if " " not in text:
            await update.message.reply_text("Формат команды: /set_deadline @username DD/MM/YYYY описание задачи...")
            return

        parts = text.split(" ", 2)

        if len(parts) < 3:
            await update.message.reply_text("Формат команды: /set_deadline @username DD/MM/YYYY описание задачи...")
            return

        username = parts[0]
        deadline = parts[1]
        task = parts[2]

        date_pattern = r"^\d{2}/\d{2}/\d{4}$"
        if not re.match(date_pattern, deadline):
            await update.message.reply_text("Дата должна быть в формате DD/MM/YYYY, например 01/03/2030.")
            return

        try:
            deadline_date = datetime.strptime(deadline, "%d/%m/%Y").date()
        except ValueError:
            await update.message.reply_text("Некорректная дата. Убедитесь, что дата в формате DD/MM/YYYY.")
            return

        add_task_to_excel(username, task, deadline)

        await update.message.reply_text(f"Задача для {username} добавлена. Дедлайн: {deadline}.")

    except Exception as e:
        if update.message:
            await update.message.reply_text(f"Ошибка: {str(e)}")
        elif update.callback_query:
            await update.callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

@restricted
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте!\nИзвините, я не понял о чем вы меня просите, мои возможности описаны в /help"
    )
