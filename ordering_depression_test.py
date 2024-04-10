import json
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()

# Загружаем тест из файла
with open('depression_test.json', 'r', encoding='utf-8') as file:
    depression_test = json.load(file)

class DepressionTest(StatesGroup):
    question = State()

@router.message(Command("depression_test"))
async def start_depression_test(message: Message, state: FSMContext):
    await message.answer(
        text=depression_test["questions"][0]
    )
    await state.set_state(DepressionTest.question)
    await state.update_data(question_index=0, score=0)

@router.message(DepressionTest.question, F.text.in_(["Да", "Нет"]))
async def answer_question(message: Message, state: FSMContext):
    user_data = await state.get_data()
    question_index = user_data["question_index"]
    score = user_data["score"]

    if message.text == "Да":
        if question_index + 1 in depression_test["scoring"]["direct_statements"]:
            score += 1
    else:
        if question_index + 1 in depression_test["scoring"]["reverse_statements"]:
            score += 1

    question_index += 1

    if question_index < len(depression_test["questions"]):
        await message.answer(
            text=depression_test["questions"][question_index]
        )
        await state.update_data(question_index=question_index, score=score)
    else:
        result = calculate_result(score)
        await message.answer(
            text=f"Ваш результат: {result}"
        )
        await state.clear()

def calculate_result(score):
    scoring = depression_test["scoring"]["interpretation"]
    if score <= scoring["no_depression"]["max_score"]:
        return "Без депрессии"
    elif score <= scoring["mild_depression"]["max_score"]:
        return "Легкая депрессия"
    elif score <= scoring["subdepressive_state"]["max_score"]:
        return "Субдепрессивное состояние"
    else:
        return "Настоящее депрессивное состояние"
