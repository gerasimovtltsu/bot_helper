import json
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

with open('psycho_tests/sos_test.json', 'r', encoding='utf8') as sos_file:
    sos_data = json.load(sos_file)

class SOSStates(StatesGroup):
    sos_answer = State()

async def start_sos(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(questions=sos_data['questions'], answers=[], index=0)
    await state.set_state(SOSStates.sos_answer)
    await message.answer(f"{sos_data['test_title']} запущен")
    await send_sos_question(message, state)

async def send_sos_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    index = user_data['index']
    questions = user_data['questions']
    sos_keyboard_builder = InlineKeyboardBuilder()
    for elem in sos_data["answers"].keys():
        sos_keyboard_builder.button(text=str(elem), callback_data=str(elem))
    sos_kbd = sos_keyboard_builder.as_markup()

    if index < len(questions):
        sos_question_text = questions[index]['text']
        if index == 0:
            await message.answer(sos_question_text, reply_markup=sos_keyboard_builder.as_markup())
        else:
            await message.edit_text(sos_question_text, reply_markup=sos_keyboard_builder.as_markup())
    else:
        await finish_test(message, state)

async def callback_query_handler(callback_query: types.CallbackQuery, state: FSMContext):
    answer = callback_query.data
    user_data = await state.get_data()
    user_data['answers'].append(answer)
    user_data['index'] += 1
    await state.set_data(user_data)
    await callback_query.answer()  # Очень важно, чтобы подтвердить получение callback
    await send_sos_question(callback_query.message, state)

async def receive_answer(message: types.Message, state: FSMContext):
    answer = message.text
    if answer not in sos_data['answers'].keys():
        await message.answer("Пожалуйста, выберите ответ из предложенных вариантов.")
        return
    user_data = await state.get_data()
    user_data['answers'].append(answer)
    user_data['index'] += 1
    await state.set_data(user_data)
    await send_sos_question(message, state)

async def finish_test(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    answers = user_data['answers']
    questions = user_data['questions']
    scale_keys = {
        "Истощение психоэнергетических ресурсов": [0, 7, 14, 21, 28, 35],  # Используем индексы с 0
        "Нарушение воли": [1, 8, 15, 22, 29, 36],
        "Эмоциональная неустойчивость": [2, 9, 16, 23, 30, 37],
        "Вегетативная неустойчивость": [3, 10, 17, 24, 31, 38],
        "Нарушения сна": [4, 11, 18, 25, 32, 39],
        "Тревога и страхи": [5, 12, 19, 26, 33, 40],
        "Дезадаптация": [6, 13, 20, 27, 34, 41]
    }
    
    scale_scores = {scale: 0 for scale in scale_keys}
    total_score = 0

    for idx, answer in enumerate(answers):
        score = 1 if answer == "Да" else 0
        total_score += score
        for scale, indexes in scale_keys.items():
            if idx in indexes:
                scale_scores[scale] += score
    # Интерпретация результатов
    if total_score <= 15:
        result = "Высокий уровень психологической устойчивости к экстремальным условиям, состояние хорошей адаптированности."
        await message.answer_photo(
            types.FSInputFile(path="pictures/high_stress_resist.jpg")
        )
        await message.answer(f"Тест завершен, спасибо за ответы.\nВаш общий результат: {total_score} баллов.\n{result}")
        
    elif total_score <= 26:
        result = "Средний уровень психологической устойчивости к экстремальным условиям, состояние удовлетворительной адаптированности."
        await message.answer_photo(
            types.FSInputFile(path="pictures/average_stress_resist.jpg")
        )
        await message.answer(f"Тест завершен, спасибо за ответы.\nВаш общий результат: {total_score} баллов.\n{result}")
    else:
        result = "Низкая стрессоустойчивость, высокий риск патологических стресс-реакций и невротических расстройств, состояние дезадаптации."
        await message.answer_photo(
            types.FSInputFile(path="pictures/low_stress_resist.jpg")
        )
        await message.answer(f"Тест завершен, спасибо за ответы.\nВаш общий результат: {total_score} баллов.\n{result}") 
    await state.clear()