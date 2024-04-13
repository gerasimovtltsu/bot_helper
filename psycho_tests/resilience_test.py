import json
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

class TestStates(StatesGroup):
    waiting_for_answer = State()

async def start_test(message: types.Message, state: FSMContext):
    await state.clear()  # Очистить предыдущее состояние, если есть
    with open('psycho_tests/resilience_test.json', 'r', encoding='utf-8') as file:
        test_data = json.load(file)
    await state.update_data(questions=test_data['questions'], answers=[], index=0)
    await state.set_state(TestStates.waiting_for_answer)
    await message.answer(f"{test_data['test_title']} запущен\nОтветьте, пожалуйста, на несколько вопросов о себе. Выбирайте тот ответ, который наилучшим образом отражает Ваше мнение. Здесь нет правильных или неправильных ответов, так как важно только Ваше мнение.\nПросьба работать в темпе, подолгу не задумываясь над ответами.\n❗️При прохождении теста вопрос будет автоматически заменяться на следующий после вашего ответа, без отправки нового сообщения.")
    await send_question(message, state)

async def send_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    index = user_data['index']
    questions = user_data['questions']
    kbd_builder = InlineKeyboardBuilder()
    buttons = ["Нет", "Скорее нет", "Скорее да", "Да"]
    for elem in buttons:
        kbd_builder.button(text=f"{elem}", callback_data=elem)

    if index < len(questions):
        question_text = questions[index]['text']
        if index == 0:
            await message.answer(question_text, reply_markup=kbd_builder.as_markup())
        else:
            await message.edit_text(question_text, reply_markup=kbd_builder.as_markup())
    else:
        await finish_test(message, state)
    
async def receive_answer(message: types.Message, state: FSMContext):
    answer = message.text
    if answer not in ['Нет', 'Скорее нет', 'Скорее да', 'Да']:
        await message.answer("Пожалуйста, выберите ответ из предложенных вариантов.")
        return
    user_data = await state.get_data()
    user_data['answers'].append(answer)
    user_data['index'] += 1
    await state.set_data(user_data)
    await send_question(message, state)

async def finish_test(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    answers = user_data['answers']
    questions = user_data['questions']

    # Словари для хранения суммарных баллов по шкалам
    scale_scores = {
        "Вовлеченность": 0,
        "Контроль": 0,
        "Принятие риска": 0
    }

    # Перевод ответов в баллы
    answer_points = {
        "Нет": 0,
        "Скорее нет": 1,
        "Скорее да": 2,
        "Да": 3
    }

    # Обработка каждого ответа
    for idx, answer in enumerate(answers):
        question = questions[idx]
        scale = question['scale']
        q_type = question['type']
        # Присваиваем баллы в зависимости от типа вопроса
        points = answer_points[answer]
        if q_type == "reverse":
            points = 3 - points  # Инвертируем баллы для обратных вопросов

        # Добавляем баллы к соответствующей шкале
        scale_scores[scale] += points
        
    
    # Вывод результатов
    result_text = "Спасибо за прохождение теста! Ваши результаты:\n"
    for scale, score in scale_scores.items():
        result_text += f"{scale}: {scale_scores[scale]} баллов\n"
        

    await message.answer(result_text)
    await state.clear()

# def register_handlers_test(dp: Dispatcher):
#     dp.register_message_handler(start_test, commands=['start_test'], state='*')
#     dp.register_message_handler(receive_answer, state=TestStates.waiting_for_answer)