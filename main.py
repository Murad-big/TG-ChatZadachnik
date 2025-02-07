from config import TOKEN
from excel_manager import initialize_excel
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler import send_reminders_sync

from handlers import (
    start, help_command, set_deadline, check_deadline,
    unknown_command, user_selection, task_selection,
    update_status, delete_task)

from google_sheet_handler import move_ideas, notify_responsible, handle_message

from datetime import datetime


def run_bot2():
    initialize_excel()

    application = Application.builder().token(TOKEN).build()
    job_queue = application.job_queue

    job_queue.run_repeating(move_ideas, interval=60, first=0)
    job_queue.run_repeating(notify_responsible, interval=60, first=10)

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_reminders_sync, "interval", days=3, args=[application], next_run_time=datetime.now())
    scheduler.start()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_deadline", set_deadline))
    application.add_handler(CommandHandler("check_deadline", check_deadline))
    application.add_handler(CallbackQueryHandler(user_selection, pattern=r"^user:"))
    application.add_handler(CallbackQueryHandler(task_selection, pattern=r"^task:"))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    application.add_handler(CallbackQueryHandler(update_status, pattern=r"^status:"))
    application.add_handler(CallbackQueryHandler(delete_task, pattern=r"^delete:"))

    application.run_polling()


if __name__ == "__main__":
    run_bot2()
