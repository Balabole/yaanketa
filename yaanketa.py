import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)

API_TOKEN = '8963003779:AAFBTsj3WBThnZzINo37TZLxKvEZZRyg9TU'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Инициализация ИИ клиента шлюза
AITUNNEL_API_KEY = 'sk-aitunnel-SyRxNmO45HRboKeVqaxZC3qBp8hCUNiF'
MODEL_TEXT = "deepseek-v4-flash"

ai_client = AsyncOpenAI(
    api_key=AITUNNEL_API_KEY,
    base_url="https://api.aitunnel.ru/v1/"
)

user_history = {}


class UserAnketa(StatesGroup):
    interests = State()  # Текст
    subjects = State()  # Текст
    goals = State()  # Текст
    employment = State()  # Кнопки
    format = State()  # Кнопки
    difficulty = State()  # Кнопки
    decision = State()  # Кнопки
    custom_track = State()  # Текст


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Заполнить анкету")],
        [KeyboardButton(text="📜 Посмотреть историю результатов")]
    ],
    resize_keyboard=True
)

employment_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟢 Низкая занятость", callback_data="emp_Низкая"),
     InlineKeyboardButton(text="🟡 Средняя занятость", callback_data="emp_Средняя")],
    [InlineKeyboardButton(text="🔴 Высокая занятость", callback_data="emp_Высокая")]
])

format_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏢 Офлайн (Очно)", callback_data="form_Офлайн"),
     InlineKeyboardButton(text="💻 Онлайн (Дистант)", callback_data="form_Онлайн")],
    [InlineKeyboardButton(text="🔄 Смешанный формат", callback_data="form_Смешанный")]
])

difficulty_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌱 Базовый уровень", callback_data="diff_Базовый"),
     InlineKeyboardButton(text="⚡ Продвинутый уровень", callback_data="diff_Продвинутый")]
])

decision_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🤖 Подобрать треки через ИИ", callback_data="act_generate")],
    [InlineKeyboardButton(text="✍️ Проанализировать мой личный вариант", callback_data="act_custom")]
])


# =====================================================================

def is_invalid_input(text: str) -> bool:
    if not text:
        return True
    words = text.split()
    for word in words:
        if len(word) > 25:
            return True
    if len(text) > 5 and len(set(text.replace(" ", ""))) == 1:
        return True
    return False


async def call_llm(full_prompt: str) -> str:
    try:
        chat_result = await ai_client.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            model=MODEL_TEXT,
            temperature=0.7
        )
        return chat_result.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        return "Техническая ошибка при связи с ИИ-сервером. Попробуйте еще раз."


# --- НЕУЯЗВИМЫЕ ХЕНДЛЕРЫ ---

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()  # Сброс любых зависших состояний при перезапуске
    await message.answer(
        f"Привет, {message.from_user.first_name}! Добро пожаловать! 🚀\n\n"
        f"Пройди быстрый опрос, и нейросеть DeepSeek разработает для тебя персональный трек развития.",
        reply_markup=main_kb
    )


@router.message(F.text == "📜 Посмотреть историю результатов")
async def show_history(message: Message):
    user_id = message.from_user.id
    if user_id not in user_history or not user_history[user_id]:
        await message.answer("У тебя пока нет сохраненной истории. Пройди анкетирование! 📋", reply_markup=main_kb)
        return

    await message.answer("🔍 Загружаю историю твоих запросов...")
    for index, past_res in enumerate(user_history[user_id], 1):
        await message.answer(f"📅 Запись №{index}\n\n{past_res}", reply_markup=main_kb)


@router.message(F.text == "📋 Заполнить анкету")
async def start_anketa(message: Message, state: FSMContext):
    await state.set_state(UserAnketa.interests)
    await message.answer("Шаг 1 из 6. Расскажи о своих интересах и увлечениях (например: IT, языки, спорт):")


@router.message(UserAnketa.interests)
async def process_interests(message: Message, state: FSMContext):
    if is_invalid_input(message.text):
        await message.answer("Пожалуйста, введи нормальный ответ текстом (без спама).")
        return
    await state.update_data(interests=message.text)
    await state.set_state(UserAnketa.subjects)
    await message.answer("Шаг 2 из 6. Какие твои любимые школьные предметы или дисциплины?")


@router.message(UserAnketa.subjects)
async def process_subjects(message: Message, state: FSMContext):
    if is_invalid_input(message.text):
        await message.answer("Пожалуйста, введи нормальный ответ.")
        return
    await state.update_data(subjects=message.text)
    await state.set_state(UserAnketa.goals)
    await message.answer("Шаг 3 из 6. Каковы твои главные цели?")


@router.message(UserAnketa.goals)
async def process_goals(message: Message, state: FSMContext):
    if is_invalid_input(message.text):
        await message.answer("Пожалуйста, введи нормальный ответ.")
        return
    await state.update_data(goals=message.text)
    await state.set_state(UserAnketa.employment)
    await message.answer("Шаг 4 из 6. Укажи желаемый уровень занятости:", reply_markup=employment_kb)


# Защита от попытки прислать текст вместо нажатия инлайн-кнопок занятости
@router.message(UserAnketa.employment)
async def text_instead_of_emp(message: Message):
    await message.answer("Пожалуйста, выберите один из вариантов на кнопках выше! 👆", reply_markup=employment_kb)


@router.callback_query(UserAnketa.employment, F.data.startswith("emp_"))
async def process_employment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(employment=callback.data.split("_")[1])
    await state.set_state(UserAnketa.format)
    await callback.message.edit_text("Шаг 5 из 6. Какой формат активности тебе подходит?", reply_markup=format_kb)


# Защита от попытки прислать текст вместо нажатия инлайн-кнопок формата
@router.message(UserAnketa.format)
async def text_instead_of_form(message: Message):
    await message.answer("Пожалуйста, выберите формат активности на кнопках! 👆", reply_markup=format_kb)


@router.callback_query(UserAnketa.format, F.data.startswith("form_"))
async def process_format(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(format=callback.data.split("_")[1])
    await state.set_state(UserAnketa.difficulty)
    await callback.message.edit_text("Шаг 6 из 6. Выбери желаемый уровень сложности программ:",
                                     reply_markup=difficulty_kb)


# Защита от попытки прислать текст вместо нажатия инлайн-кнопок сложности
@router.message(UserAnketa.difficulty)
async def text_instead_of_diff(message: Message):
    await message.answer("Пожалуйста, выберите уровень сложности на кнопках! 👆", reply_markup=difficulty_kb)


@router.callback_query(UserAnketa.difficulty, F.data.startswith("diff_"))
async def process_difficulty(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(difficulty=callback.data.split("_")[1])
    await state.set_state(UserAnketa.decision)
    await callback.message.edit_text("Анкета успешно собрана! Выбери режим работы ИИ:", reply_markup=decision_kb)


# Защита от попытки прислать текст на этапе выбора решения
@router.message(UserAnketa.decision)
async def text_instead_of_decision(message: Message):
    await message.answer("Пожалуйста, выберите нужный режим на кнопках! 👆", reply_markup=decision_kb)


# РЕЖИМ 1: КРЕАТИВНАЯ ГЕНЕРАЦИЯ ТРЕКОВ
@router.callback_query(UserAnketa.decision, F.data == "act_generate")
async def decision_generate(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    anketa_data = await state.get_data()
    await state.clear()

    await callback.message.delete()
    status_msg = await callback.message.answer("⏳ Модуль ИИ разрабатывает для тебя персональные треки...")
    await bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    prompt = (
        "Ты — продвинутый ИИ-эксперт по профориентации. Твоя задача — проанализировать анкету пользователя "
        "и придумать ровно 3 конкретных и наиболее подходящих образовательных трека (курсы, секции, кружки).\n\n"
        "ТРЕБОВАНИЯ К ОФОРМЛЕНИЮ:\n"
        "1. Пиши обычным простым текстом. ВООБЩЕ никогда не используй символы звездочек (*) для выделения слов!\n"
        "2. Сделай ответ красивым: используй подходящие тематические эмодзи для каждого пункта.\n"
        "3. Кратко поясни для каждого придуманного трека, почему он идеально подходит под параметры пользователя.\n"
        "4. Разделяй блоки понятными абзацами. Обращайся на 'ты'.\n\n"
        f"Данные анкеты пользователя:\n"
        f"- Интересы: {anketa_data.get('interests')}\n"
        f"- Любимые предметы: {anketa_data.get('subjects')}\n"
        f"- Главные цели: {anketa_data.get('goals')}\n"
        f"- Доступная занятость: {anketa_data.get('employment')}\n"
        f"- Формат активности: {anketa_data.get('format')}\n"
        f"- Уровень сложности: {anketa_data.get('difficulty')}"
    )

    response = await call_llm(prompt)
    clean_res = response.replace("*", "")

    if user_id not in user_history:
        user_history[user_id] = [clean_res]
    else:
        user_history[user_id].append(clean_res)

    await status_msg.delete()
    await callback.message.answer(f"🤖 **Сгенерированные направления от ИИ:**\n\n{clean_res}", reply_markup=main_kb)


# РЕЖИМ 2: АНАЛИЗ СВОЕГО ВАРИАНТА
@router.callback_query(UserAnketa.decision, F.data == "act_custom")
async def decision_custom(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(UserAnketa.custom_track)
    await callback.message.edit_text(
        "✍️ Введи название или описание курса/кружка, который ты нашел сам, и ИИ проанализирует его:")


@router.message(UserAnketa.custom_track)
async def process_custom_track(message: Message, state: FSMContext):
    if is_invalid_input(message.text):
        await message.answer("Пожалуйста, введи нормальное название курса без спама символами.")
        return

    user_id = message.from_user.id
    anketa_data = await state.get_data()
    user_track = message.text
    await state.clear()

    status_msg = await message.answer("⏳ Модуль ИИ проводит глубокий анализ вашего трека...")
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    prompt = (
        "Ты — ИИ-эксперт по профориентации. Пользователь заполнил анкету и предлагает свой собственный вариант трека для анализа.\n"
        f"ВАРИАНТ ПОЛЬЗОВАТЕЛЯ ДЛЯ АНАЛИЗА: {user_track}\n\n"
        "Твоя задача — сделать экспертный разбор этого направления на основе данных его анкеты:\n"
        "1. Подходит ли этот трек под его цели, формат, сложность и интересы?\n"
        "2. Выдели ключевые ПЛЮСЫ и возможные МИНУСЫ/риски для пользователя.\n"
        "3. Дай итоговый вердикт и совет.\n\n"
        "ТРЕБОВАНИЯ К ОФОРМЛЕНИЮ:\n"
        "- Пиши простым текстом БЕЗ ЗВЕЗДОЧЕК (*).\n"
        "- Используй красивые эмодзи для структуры (Плюсы, Минусы, Вердикт).\n\n"
        f"АНКЕТА ЮЗЕРА:\n- Интересы: {anketa_data.get('interests')}\n- Предметы: {anketa_data.get('subjects')}\n"
        f"- Цели: {anketa_data.get('goals')}\n- Занятость: {anketa_data.get('employment')}\n"
        f"- Формат: {anketa_data.get('format')}\n- Сложность: {anketa_data.get('difficulty')}"
    )

    response = await call_llm(prompt)
    clean_res = response.replace("*", "")

    formatted_history = f"Анализ личного трека '{user_track}':\n\n{clean_res}"
    if user_id not in user_history:
        user_history[user_id] = [formatted_history]
    else:
        user_history[user_id].append(formatted_history)

    await status_msg.delete()
    await message.answer(f"✍️ **Результаты ИИ-анализа твоего трека:**\n\n{clean_res}", reply_markup=main_kb)


# Улавливатель ложных инлайн-кликов из прошлых сессий
@router.callback_query()
async def old_callbacks_handler(callback: CallbackQuery):
    await callback.answer("Эта кнопка устарела. Начните опрос заново через меню! 📋", show_alert=True)


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())