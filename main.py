import logging
import json

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN
import keyboard_handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Чтение конфигурации для клавиатуры
with open("keyboard.json", "r", encoding='utf8') as kbd_layout:
    kbd_json = json.load(kbd_layout)
keyboard = ReplyKeyboardMarkup(**kbd_json)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Добро пожаловать! Выберите действие на появивщейся клавиатуре. Для повторного вызова меню отправьте команду /start или /menu",
        reply_markup=keyboard
    )

async def forward_all_messages_to_specialist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('in_consultation') and update.effective_chat.id != keyboard_handlers.SPECIALIST_CHAT_ID:
        await context.bot.forward_message(chat_id=keyboard_handlers.SPECIALIST_CHAT_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        await update.message.reply_text(f"Ваше сообщение было отправлено специалисту. ID пользователя: {update.effective_chat.id}. Для того, чтобы специалист мог связаться с Вами - откройте возможность писать людям не в Ваших контактах")
    else:
        await update.message.reply_text(f"Вы не вошли в режим консультации или Вы являетесь администратором", reply_markup=keyboard)

async def end_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('in_consultation'):
        context.user_data['in_consultation'] = False
        await update.message.reply_text(f'Консультация завершена. ID пользователя: {update.effective_chat.id}')

async def list_open_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Здесь вы можете получить список всех открытых заявок из какого-то хранилища данных
    # Например, можно использовать базу данных или какой-то другой метод хранения данных
    open_requests = []

    if open_requests:
        message = "Список открытых заявок:\n"
        for request in open_requests:
            message += f"- Заявка от {request['user_id']}: {request['text']}\n"
    else:
        message = "Нет открытых заявок."

    await update.message.reply_text(message)

async def answer_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 2:
        try:
            request_id = int(context.args[0])  # ID заявки
            message_text = " ".join(context.args[1:])  # Текст ответа
            await context.bot.send_message(chat_id=request_id, text=message_text)
            await update.message.reply_text("Ответ на заявку отправлен пользователю")
        except ValueError:
            await update.message.reply_text("Некорректный ID заявки")
    else:
        await update.message.reply_text("Использование: /answer {ID_заявки} {ваш ответ}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler(['start', 'menu'], start)
    application.add_handler(start_handler)

    application.add_handler(MessageHandler(filters.Regex('^Консультация со специалистом$'), keyboard_handlers.handle_consultation))
    application.add_handler(MessageHandler(filters.Regex('^Информация о боте$'), keyboard_handlers.handle_bot_info))

    application.add_handler(MessageHandler(filters.Text() & filters.ChatType.PRIVATE, forward_all_messages_to_specialist))
    application.add_handler(MessageHandler(filters.User(user_id=keyboard_handlers.SPECIALIST_CHAT_ID) & filters.ChatType.PRIVATE, keyboard_handlers.forward_to_user))
    
    application.add_handler(CommandHandler('answer', answer_request))
    application.add_handler(CommandHandler('end_consultation', end_consultation))
    application.add_handler(CommandHandler('open_requests', list_open_requests))
    
    application.run_polling()