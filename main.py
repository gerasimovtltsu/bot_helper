import asyncio
import json
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
# from aiogram.utils import executor
from config import BOT_TOKEN, ADMIN_BOT_TOKEN
import keyboard_handlers

logging.basicConfig(level=logging.INFO)

admin_to_user_map = {} # словарь для хранения соответствия между сообщениями в чате админа и идентификаторами чатов пользователей

with open("keyboard.json", "r", encoding='utf8') as kbd_layout:
    kbd_json = json.load(kbd_layout)

keyboard = ReplyKeyboardMarkup(**kbd_json)

bot = Bot(token=BOT_TOKEN)
admin_bot = Bot(token=ADMIN_BOT_TOKEN)
dp = Dispatcher()

admin_dp = Dispatcher()

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать! Выберите действие на появивщейся клавиатуре. Для повторного вызова меню отправьте команду /start",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text == 'Консультация со специалистом')
async def handle_consultation(message: types.Message, state: FSMContext):
    await keyboard_handlers.handle_consultation(message, state)

@dp.message(lambda message: message.text == 'Информация о боте')
async def handle_bot_info(message: types.Message, state: FSMContext):
    await keyboard_handlers.handle_bot_info(message, state)

@dp.message(lambda message: message.from_user.id == keyboard_handlers.SPECIALIST_CHAT_ID)
async def forward_to_user(message: types.Message, state: FSMContext):
    await keyboard_handlers.forward_to_user(message, state)

@dp.message()
async def forward_all_messages_to_specialist(message: types.Message, state: FSMContext):
    await keyboard_handlers.forward_to_specialist(message, state)

@dp.message(Command('end_consultation'))
async def end_consultation(message: types.Message, state: FSMContext):
    await keyboard_handlers.end_consultation(message, state)

@dp.message(Command('open_requests'))
async def list_open_requests(message: types.Message, state: FSMContext):
    await keyboard_handlers.list_open_requests(message, state)

@dp.message(Command('answer'))
async def answer_request(message: types.Message, state: FSMContext):
    await keyboard_handlers.answer_request(message, state)

async def forward_to_admin(message: types.Message):
    forwarded_message = await admin_bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id)
    admin_to_user_map[forwarded_message.message_id] = message.chat.id

@admin_dp.message(lambda message: message.reply_to_message and message.reply_to_message.message_id in admin_to_user_map)
async def handle_admin_response(message: types.Message):
    user_chat_id = admin_to_user_map[message.reply_to_message.message_id]
    await admin_bot.send_message(chat_id=user_chat_id, text=message.text)

@admin_dp.message(lambda message: message.reply_to_message and message.reply_to_message.message_id in keyboard_handlers.specialist_to_user_map)
async def handle_specialist_response(message: types.Message):
    user_chat_id, original_message_id = keyboard_handlers.specialist_to_user_map[message.reply_to_message.message_id]
    await bot.send_message(chat_id=user_chat_id, text=message.text, reply_to_message_id=original_message_id)

@dp.message()
async def handle_message(message: types.Message):
    await forward_to_admin(message)


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())