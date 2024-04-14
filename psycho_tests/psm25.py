import json
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

with open('psycho_tests/psm25.json', 'r', encoding='utf8') as psm_file:
        psm_data = json.load(psm_file)

class PSMStates(StatesGroup):
    psm_answer = State()

async def start_psm(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(questions=psm_data['questions'], answers=[], index=0)
    await state.set_state(PSMStates.psm_answer)
    await message.answer(f"{psm_data['test_title']} запущен\nПредлагается ряд утверждений, характеризующих психическое состояние.\nОцените, пожалуйста, Ваше состояние за последнюю неделю с помощью 8-балльной шкалы. Для этого на бланке опросника рядом с каждым утверждением обведите (поставьте) число от 1 до 8, которое наиболее точно определяет ваши переживания.\nЗдесь нет неправильных или ошибочных ответов.\nОтвечайте как можно искреннее.\nДля выполнения теста потребуется приблизительно пять минут.\nЦифры от 1 до 8 означают частоту переживаний.\n❗️При прохождении теста вопрос будет автоматически заменяться на следующий после вашего ответа, без отправки нового сообщения.")
    await message.answer("Для выхода из теста отправьте команду <code>/start</code>", parse_mode='HTML')
    await send_psm_question(message, state)

async def send_psm_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    index = user_data['index']
    questions = user_data['questions']
    psm_kbd_builder = InlineKeyboardBuilder()
    for elem in range(1, 9):
        psm_kbd_builder.button(text=str(elem), callback_data=str(elem))
    psm_kbd = psm_kbd_builder.as_markup()
    
    if index < len(questions):
        psm_question_text = questions[index]['text']
        if index == 0:
            await message.answer(psm_question_text, reply_markup=psm_kbd_builder.as_markup())
        else:
            await message.edit_text(psm_question_text, reply_markup=psm_kbd_builder.as_markup())
    else:
        await finish_test(message, state)

async def callback_query_handler(callback_query: types.CallbackQuery, state: FSMContext):
    answer = callback_query.data
    user_data = await state.get_data()
    user_data['answers'].append(int(answer))
    user_data['index'] += 1
    await state.set_data(user_data)
    await callback_query.answer()  # Очень важно, чтобы подтвердить получение callback
    await send_psm_question(callback_query.message, state)

async def receive_answer(message: types.Message, state: FSMContext):
    answer = message.text
    if answer not in psm_data['scales']:
        await message.answer("Пожалуйста, выберите ответ из предложенных вариантов.")
        return
    user_data = await state.get_data()
    user_data['answers'].append(answer)
    user_data['index'] += 1
    await state.set_data(user_data)
    await send_psm_question(message, state)

async def finish_test(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    total_score = sum(user_data['answers'])  # Просто суммируем ответы
    result_text = f"Спасибо за прохождение теста!\nВаши результаты:\nВы набрали {total_score} баллов\nРезультаты прохождения теста:\n"
    points = psm_data['scoring']
    if total_score >= points['high_stress']['min_score']:
        result_text += points['high_stress']['description']
        await message.answer_photo(
            types.FSInputFile(path="pictures/high_stress.jpg")
        )
    elif points['medium_stress']['max_score'] >= total_score >= points['medium_stress']['min_score']:
        result_text += points['medium_stress']['description']
        await message.answer_photo(
            types.FSInputFile(path="pictures/medium_stress.jpg")
        )
    else:
        result_text += points['low_stress']['description']
        await message.answer_photo(
            types.FSInputFile(path="pictures/low_stress.jpg")
        )
    await message.answer(result_text)
    await state.clear()
