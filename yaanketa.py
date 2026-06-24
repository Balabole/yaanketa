import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery

logging.basicConfig(level=logging.INFO)

API_TOKEN = '8963003779:AAFbWjq890GQd3fngSo46rvpHyzRFdyi3Ds'

AITUNNEL_API_KEY = 'sk-aitunnel-SyRxNmO45HRboKeVqaxZC3qBp8hCUNiF'
AITUNNEL_URL_TEXT = "https://api.aitunnel.ru/v1/chat/completions"
MODEL_TEXT = "deepseek-v4-flash"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()


class UserAnketa(StatesGroup):
    interests = State()  # 1. Сфера интересов
    subjects = State()  # 2. Любимые предметы
    goals = State()  # 3. Цели
    employment = State()  # 4. Уровень занятости
    format = State()  # 5. Формат активности
    difficulty = State()  # 6. Желаемая сложность


main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📋 Начать анкетирование")]],
    resize_keyboard=True
)

employment_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Низкая (пару часов в неделю)", callback_data="emp_Низкая")],
    [InlineKeyboardButton(text="Средняя (регулярные занятия)", callback_data="emp_Средняя")],
    [InlineKeyboardButton(text="Высокая (полное погружение)", callback_data="emp_Высокая")]
])

format_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏢 Офлайн (Очно)", callback_data="form_Офлайн (Очно)")],
    [InlineKeyboardButton(text="💻 Онлайн (Дистанционно)", callback_data="form_Онлайн (Дистанционно)")],
    [InlineKeyboardButton(text="🔄 Смешанный формат", callback_data="form_Смешанный формат")]
])

difficulty_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢 Базовый (Для новичков)", callback_data="diff_Базовый")],
    [InlineKeyboardButton(text="🟡 Продвинутый (С опытом)", callback_data="diff_Продвинутый")]
])


# АСИНХРОННЫЙ МОДУЛЬ ИИ ОБРАБОТКИ (Написано исключительно ИИ)

# ИИ
# Функция отправки параметров анкеты в продвинутую текстовую модель через aitunnel
async def get_llm_recommendation(anketa_data: dict) -> str:
    """Отправка собранной анкеты в ИИ для получения текстовых рекомендаций"""
    headers = {
        "Authorization": f"Bearer {AITUNNEL_API_KEY}",
        "Content-Type": "application/json"
    }

    interests = anketa_data.get('interests') or "Не указано"
    subjects = anketa_data.get('subjects') or "Не указано"
    goals = anketa_data.get('goals') or "Не указано"
    employment = anketa_data.get('employment') or "Не указано"
    format_act = anketa_data.get('format') or "Не указано"
    difficulty = anketa_data.get('difficulty') or "Не указано"

    full_prompt = (
        "Ты — продвинутый ИИ-эксперт по профориентации. "
        "Изучи анкету пользователя и предложи 3 конкретных подходящих направления (кружки, секции или курсы). "
        "ВАЖНО: Пиши обычным простым текстом, вообще никогда не используй символы звездочек для выделения слов! "
        "Отвечай кратко, структурировано по пунктам, без лишней воды. Обращайся на 'ты'.\n\n"
        f"Данные анкеты:\n"
        f"- Интересы: {interests}\n"
        f"- Любимые предметы: {subjects}\n"
        f"- Цели: {goals}\n"
        f"- Занятость: {employment}\n"
        f"- Формат: {format_act}\n"
        f"- Сложность: {difficulty}"
    )

    payload = {
        "model": MODEL_TEXT,
        "messages": [
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        "temperature": 0.7
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(AITUNNEL_URL_TEXT, json=payload, headers=headers, timeout=25) as response:
                if response.status == 200:
                    result_json = await response.json()
                    return result_json['choices'][0]['message']['content']
                else:
                    response_text = await response.text()
                    logging.error(f"Ошибка API {MODEL_TEXT}: {response.status}. Ответ: {response_text}")
                    return "Не удалось сгенерировать ответ. Попробуйте еще раз чуть позже."
    except Exception as e:
        logging.error(f"Ошибка при запросе к LLM: {e}")
        return "Произошла техническая ошибка при связи с ИИ-сервером."



@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! Добро пожаловать в систему подбора образовательных треков! 🚀\n"
        f"Пройди опрос из 6 шагов, и наш продвинутый ИИ-помощник составит для тебя "
        f"индивидуальные рекомендации.",
        reply_markup=main_kb
    )


@router.message(F.text == "📋 Начать анкетирование")
async def start_anketa(message: Message, state: FSMContext):
    await state.set_state(UserAnketa.interests)
    await message.answer("Шаг 1 из 6. Расскажи о своих интересах и увлечениях (например: IT, языки, спорт):")


@router.message(UserAnketa.interests)
async def process_interests(message: Message, state: FSMContext):
    await state.update_data(interests=message.text)
    await state.set_state(UserAnketa.subjects)
    await message.answer("Шаг 2 из 6. Какие твои любимые школьные предметы, курсы или дисциплины?")


@router.message(UserAnketa.subjects)
async def process_subjects(message: Message, state: FSMContext):
    await state.update_data(subjects=message.text)
    await state.set_state(UserAnketa.goals)
    await message.answer(
        "Шаг 3 из 6. Каковы твои главные цели (например: собрать проект, найти хобби, развить навыки)?")


@router.message(UserAnketa.goals)
async def process_goals(message: Message, state: FSMContext):
    await state.update_data(goals=message.text)
    await state.set_state(UserAnketa.employment)
    await message.answer("Шаг 4 из 6. Укажи желаемый уровень занятости:", reply_markup=employment_kb)


@router.callback_query(UserAnketa.employment)
async def process_employment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(employment=callback.data.split("_")[1])
    await callback.answer()
    await state.set_state(UserAnketa.format)
    await callback.message.edit_text("Шаг 5 из 6. Какой формат активности тебе подходит?", reply_markup=format_kb)


@router.callback_query(UserAnketa.format)
async def process_format(callback: CallbackQuery, state: FSMContext):
    await state.update_data(format=callback.data.split("_")[1])
    await callback.answer()
    await state.set_state(UserAnketa.difficulty)
    await callback.message.edit_text("Шаг 6 из 6. Выбери желаемый уровень сложности программ:",
                                     reply_markup=difficulty_kb)


@router.callback_query(UserAnketa.difficulty)
async def process_difficulty(callback: CallbackQuery, state: FSMContext):
    diff_val = callback.data.split("_")[1]
    await state.update_data(difficulty=diff_val)
    await callback.answer()

    full_anketa = await state.get_data()
    await state.clear()

    await callback.message.delete()
    status_msg = await callback.message.answer("⏳ Модуль искусственного интеллекта анализирует ваши ответы...")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    # === ТОЛЬКО ИИ ===
    recommendations = await get_llm_recommendation(full_anketa)

    # Дополнительная ручная фильтрация текста от любых случайных символов markdown звездочек
    clean_recommendations = recommendations.replace("*", "")

    await status_msg.delete()
    await callback.message.answer(
        f"📊 Рекомендации по твоей индивидуальной траектории:\n\n{clean_recommendations}",
        reply_markup=main_kb
    )

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())