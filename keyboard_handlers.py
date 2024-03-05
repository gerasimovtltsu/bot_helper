from telegram import Update
from telegram.ext import ContextTypes

SPECIALIST_CHAT_ID = 288957466
active_consultations = {}

from telegram import Update
from telegram.ext import ContextTypes

async def handle_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['in_consultation'] = True
    active_consultations[SPECIALIST_CHAT_ID] = update.effective_chat.id
    await update.message.reply_text('Вы вошли в режим консультации. Напишите ваш вопрос, и специалист вам ответит.')

async def forward_to_specialist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('in_consultation'):
        await context.bot.forward_message(chat_id=SPECIALIST_CHAT_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        await update.message.reply_text("Ваш запрос был отправлен консультанту. Пожалуйста, ожидайте ответа.")

async def forward_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        await context.bot.forward_message(chat_id=update.message.reply_to_message.forward_from.id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        await update.message.reply_text("Ответ от консультанта отправлен вам.")

async def answer_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 2:
        try:
            user_id = int(context.args[0])
            message_text = " ".join(context.args[1:])
            await second_bot.send_message(chat_id=user_id, text=message_text)
            await update.message.reply_text("Ответ отправлен пользователю")
        except ValueError:
            await update.message.reply_text("Некорректный ID пользователя")
    else:
        await update.message.reply_text("Использование: /answer {id_пользователя} {ваш ответ}")

async def handle_bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Здесь будет информация о боте.')