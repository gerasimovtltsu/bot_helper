from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

SPECIALIST_CHAT_ID = 288957466
active_consultations = {}

class UserState(StatesGroup):
    in_consultation = State()
    not_consult = State()


async def handle_consultation(message: types.Message, state: FSMContext):
    await state.set_state(UserState.in_consultation)
    active_consultations[SPECIALIST_CHAT_ID] = message.chat.id
    await message.reply('Вы вошли в режим консультации\. Напишите Ваш вопрос, и специалист Вам ответит\. Чтобы выйти из режима консультации отправьте сообщение `Завершить консультацию`', parse_mode='MarkdownV2')
    if message.text == 'Завершить консультацию':
            await end_consultation(message, state.get_state())

async def forward_to_specialist(message: types.Message, state: FSMContext):
    if await state.get_state() == UserState.in_consultation.state:
        await message.bot.forward_message(chat_id=SPECIALIST_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.answer("Ваш запрос был отправлен консультанту. Пожалуйста, ожидайте ответа.")

async def forward_to_user(message: types.Message, state: FSMContext):
    if message.reply_to_message:
        await message.bot.forward_message(chat_id=message.reply_to_message.forward_from.id, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.answer("Ответ отправлен пользователю. Спасибо за оперативный ответ")

async def end_consultation(message: types.Message, state: FSMContext):
    if await state.get_state() == UserState.in_consultation.state:
        if message.text == 'Завершить консультацию':
            await message.answer('Консультация завершена! Спасибо за обращение!')
            await state.clear()

# def register_handlers(dp: Dispatcher):
#     dp.register_message_handler(handle_consultation, commands=['start_consultation'], state=UserState.in_consultation)
#     dp.register_message_handler(forward_to_specialist, state=UserState.in_consultation)
#     dp.register_message_handler(forward_to_user, state=UserState.in_consultation)
#     dp.register_message_handler(end_consultation, commands=['end_consultation'], state='')
