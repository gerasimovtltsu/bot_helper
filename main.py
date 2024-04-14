import json
import logging

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_BOT_TOKEN
import keyboard_handlers

import psycho_tests.resilience_test


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

admin_to_user_map = {} # словарь для хранения соответствия между сообщениями в чате админа и идентификаторами чатов пользователей

with open("keyboard.json", "r", encoding='utf8') as kbd_layout:
    kbd_json = json.load(kbd_layout)

keyboard = ReplyKeyboardMarkup(**kbd_json)

bot = Bot(token=BOT_TOKEN)
admin_bot = Bot(token=ADMIN_BOT_TOKEN)
router = Router()

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)
admin_dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer_photo(
        types.FSInputFile(path="pictures/welcome_picture.jpg")
    )
        
    await message.answer(
        text= "🌿 Добро пожаловать в чат-бота психологической помощи!\n" + \
        "🌟 Здесь Вы можете получить поддержку и консультацию, когда Вам это необходимо.\n" + \
        "⏰ Наш чат-бот доступен для Вас круглосуточно, в любое удобное время.\n" + \
        "📞 Для консультации отправьте запрос, выбрав в меню пункт 'Консультация со специалистом'. Наши специалисты обязательно с Вами свяжутся и ответят на Ваши вопросы.\n" + \
        "✨ Пожалуйста, напишите, какая помощь Вам необходима, и мы с удовольствием поможем в Вашем путешествии к психологическому благополучию.\n" + \
        "🌺 Не стесняйтесь обращаться за поддержкой, Вы заслуживаете заботу и внимание!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@dp.message(lambda message: message.text == '🙋 Консультация со специалистом')
async def handle_consultation(message: types.Message, state: FSMContext):
    await state.clear()  # Явный сброс состояния
    await keyboard_handlers.handle_consultation(message, state)

@dp.message(lambda message: message.from_user.id == keyboard_handlers.SPECIALIST_CHAT_ID)
async def forward_to_user(message: types.Message, state: FSMContext):
    await keyboard_handlers.forward_to_user(message, state)

@dp.message(lambda message: message.text == "📝 Тест жизнестойкости (С. Мадди, адаптация Д.А. Леонтьева)")
async def handle_test(message: types.Message, state: FSMContext):
    await state.clear()
    await psycho_tests.resilience_test.start_test(message, state)

@dp.message()
async def forward_all_messages_to_specialist(message: types.Message, state: FSMContext):
    if message.text != "Завершить консультацию":  # Проверяем текст сообщения, а не объект сообщения
        await keyboard_handlers.forward_to_specialist(message, state)
    else:
        await end_consultation(message, state)  # Передаем объект сообщения и объект состояния

@dp.message(Command('end_consultation'))
async def end_consultation(message: types.Message, state: FSMContext):
    await keyboard_handlers.end_consultation(message, state)

@dp.message(lambda message: message.text == 'Завершить консультацию')
async def end_consultation_text(message: types.Message, state: FSMContext):
    await keyboard_handlers.end_consultation(message, state)

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

@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "TestStates:waiting_for_answer":
        return # Пропустить обработку, если состояние не совпадает

    answer = callback_query.data
    await callback_query.answer()  # Отправляем пустой ответ на callback, чтобы убрать "часики" у пользователя
    
    if answer not in ['Нет', 'Скорее нет', 'Скорее да', 'Да']:
        await callback_query.message.answer("Пожалуйста, выберите ответ из предложенных вариантов.")
        return

    user_data = await state.get_data()
    user_data['answers'].append(answer)
    user_data['index'] += 1
    await state.set_data(user_data)
    await psycho_tests.resilience_test.send_question(callback_query.message, state)

async def main():
    await dp.start_polling(bot)
    await admin_dp.start_polling(admin_bot)

if __name__ == '__main__':
    import asyncio
    # psycho_tests.resilience_test.register_handlers_test(dp)
    asyncio.run(main())