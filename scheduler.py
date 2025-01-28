import asyncio
from config import ALLOWED_CHAT_ID
from datetime import datetime
from excel_manager import read_excel_data

def send_reminders_sync(application):
    asyncio.run(send_reminders(application))

async def send_reminders(application):
    try:
        names, desc, dates, statuses = read_excel_data()
        chat_id = ALLOWED_CHAT_ID

        reminders = []
        today = datetime.today().date()

        for i in range(len(names)):
            task_date = datetime.strptime(dates[i], "%d/%m/%Y").date()
            days_left = (task_date - today).days
            if statuses[i] != "Done" and days_left <= 3:
                reminders.append(
                    f"🔔 Напоминание: Задача '{desc[i]}' для @{names[i]} с дедлайном {dates[i]} (осталось {days_left} дней)"
                )

        if reminders:
            message = "\n\n".join(reminders)
            await application.bot.send_message(chat_id=chat_id, text=message)
        else:
            await application.bot.send_message(chat_id=chat_id, text="✅ Все задачи выполнены или нет задач с приближающимся дедлайном.")
    except Exception as e:
        print(f"Ошибка при отправке напоминаний: {str(e)}")