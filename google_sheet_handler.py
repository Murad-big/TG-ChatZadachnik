import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import ALLOWED_CHAT_ID
from utils import restricted


def authenticate_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open_by_key('1c0-fYPJO3YAU7JvP2WHwSS9MOB22h07PrHqXDYHFWc0')


async def move_ideas(context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = authenticate_google_sheets()
        proposed_sheet = sheet.worksheet('Предложенные')
        approved_sheet = sheet.worksheet('Одобренные')
        implementation_sheet = sheet.worksheet('На реализацию')

        for row in proposed_sheet.get_all_records():
            if row['Статус'] == 'Одобренные' and row['Перемещено'] != '✔':
                approved_sheet.append_row([
                    row['Пользователь'], row['Идея'], row['Дата'], row['Статус'], '❌'
                ])
                cell = proposed_sheet.find(row['Идея'])
                if cell:
                    proposed_sheet.update_cell(cell.row, 5, '✔')

        rows = approved_sheet.get_all_records()
        rows_to_delete = []

        for index, row in enumerate(rows, start=2):
            if row['Статус'] == 'На реализацию' and row['Перемещено'] != '✔':
                implementation_sheet.append_row([
                    row['Пользователь'], row['Идея'], row['Дата'], '', '3'
                ])
                rows_to_delete.append(index)

        for i in sorted(rows_to_delete, reverse=True):
            approved_sheet.delete_rows(i)
    except Exception as e:
        print(e)


@restricted
async def notify_responsible(context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = authenticate_google_sheets().worksheet('На реализацию')
        rows = sheet.get_all_records()

        for row in rows:
            if row.get('Ответственный') and row.get('Уведомлено') != '✔':
                username = row.get('Ответственный', '')
                idea = row.get('Идея', '')
                days = int(row.get('Сколько дней', 0))
                date_str = row.get('Дата', '')

                try:
                    if " " in date_str:
                        task_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        task_date = datetime.strptime(date_str, "%Y-%m-%d")

                    deadline_date = task_date + timedelta(days=days)
                    formatted_date = deadline_date.strftime("%d/%m/%Y")

                    message = f"/set_deadline @{username} {formatted_date} {idea}"
                    await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=message)

                    cell = sheet.find(row['Идея'])
                    if cell:
                        sheet.update_cell(cell.row, 6, '✔')
                except Exception as e:
                    print(e)

    except Exception as e:
        print(e)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Функция move_ideas вызвана!")
    message = update.message.text
    if '#идея' in message.lower():
        try:
            sheet = authenticate_google_sheets().worksheet('Предложенные')
            cleaned_message = message.replace('#идея', '').strip()
            existing_ideas = [row['Идея'] for row in sheet.get_all_records()]

            if cleaned_message in existing_ideas:
                await update.message.reply_text('Такая идея уже существует!')
                return

            sheet.append_row([
                update.message.from_user.username,
                cleaned_message,
                update.message.date.strftime('%Y-%m-%d %H:%M:%S'),
                'Предложенные',
                '❌'
            ])

            await update.message.reply_text('Идея добавлена!')
        except Exception as e:
            print(e)
            await update.message.reply_text('Ошибка при добавлении идеи.')
