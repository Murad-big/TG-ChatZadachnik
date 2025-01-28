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

from datetime import datetime


def run_bot2():
    initialize_excel()

    application = Application.builder().token(TOKEN).build()

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_reminders_sync, "interval", days=3, args=[application], next_run_time=datetime.now())
    scheduler.start()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_deadline", set_deadline))
    application.add_handler(CommandHandler("check_deadline", check_deadline))
    application.add_handler(CallbackQueryHandler(user_selection, pattern=r"^user:"))
    application.add_handler(CallbackQueryHandler(task_selection, pattern=r"^task:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(CallbackQueryHandler(update_status, pattern=r"^status:"))
    application.add_handler(CallbackQueryHandler(delete_task, pattern=r"^delete:"))

    application.run_polling()
if __name__ == "__main__":
    run_bot2()