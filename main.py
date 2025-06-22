import asyncio
import logging
import os
from datetime import datetime
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

from flask import Flask
import db


# Конфигурация
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Flask keep-alive
app = Flask(__name__)
@app.route('/')
def home():
    return "✅ Бот работает (Flask)!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()


# Функция безопасной отправки длинных сообщений с HTML и ссылками
async def send_long_message(chat_id: int, text: str):
    MAX_LENGTH = 4000
    # Разбиваем текст по границам длины, стараясь не резать теги и строки
    start = 0
    while start < len(text):
        # Ищем конец для среза
        end = min(start + MAX_LENGTH, len(text))
        # Чтобы не резать теги и слова, откатываем к предыдущему \n или пробелу, если не в начале
        if end < len(text):
            last_newline = text.rfind('\n', start, end)
            if last_newline > start:
                end = last_newline + 1
        part = text[start:end].strip()
        if part:
            await bot.send_message(chat_id, part, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
        start = end


# Клавиатуры
main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔥 ПОПАСТЬ В ЧАТ С СИГНАЛАМИ", callback_data="join_chat_info")],
    [InlineKeyboardButton(text="📝 ОТЗЫВЫ", callback_data="reviews")],
    [InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="stats")],
    [InlineKeyboardButton(text="😈 ОБО МНЕ", callback_data="about")]
])
admin_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="📤 Рассылка"), KeyboardButton(text="📈 Статистика")],
    [KeyboardButton(text="📥 Экспорт .xlsx"), KeyboardButton(text="➕ Добавить в чат")]
])

broadcast_mode = {}
add_mode = {}

# Текст приветственного сообщения с полной подборкой статей, включая потерянную
WELCOME_TEXT = (
    "👋 Привет друг, здесь можно получить доступ к нашему торговому комьюнити.\n\n"
    "Здесь тебя ждут:\n"
    "🔹 сигналы на сделки\n"
    "🔹 инвестиционные идеи\n"
    "🔹 обучающие уроки\n\n"
    "Для того, чтобы попасть в него, тебе необходимо зарегистрироваться на бирже BingX и пополнить баланс.\n\n"
    "Для удобства прикрепляю инструкции:\n\n"
    "📘 <a href='https://telegra.ph/Kak-zaregistrirovatsya-na-kripto-birzhe-BingX-06-13'>КАК ЗАРЕГИСТРИРОВАТЬСЯ НА БИРЖЕ BingX</a>\n\n"
    "📘 <a href='https://telegra.ph/Instrukciya-po-perenosu-KYC-06-13'>ПОШАГОВАЯ ИНСТРУКЦИЯ ПЕРЕНОСА ВЕРИФИКАЦИИ</a>\n\n"
    "📘 <a href='https://telegra.ph/Kak-kupit-kriptovalyutu-na-birzhe-BingX-06-13'>КАК КУПИТЬ КРИПТОВАЛЮТУ ЧЕРЕЗ P2P</a>\n\n"
    "📘 <a href='https://telegra.ph/Rabota-so-sdelkami-na-BingX-06-13'>РАБОТА СО СДЕЛКАМИ НА BingX</a>\n\n"
    "📘 <a href='https://telegra.ph/Otkrytie-sdelki-LONG-i-SHORT-06-14'>ОТКРЫТИЕ LONG/SHORT СДЕЛОК</a>\n\n"
    "Если у тебя уже есть аккаунт на BingX — ты можешь перенести его под мою ссылку. Это несложно и займет 15 минут.\n\n"
    "Вопросы — пиши: @Gold_Denys"
    parse_mode=ParseMode.HTML
)


# Хендлеры
@dp.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    try:
        db.add_user(user.id, user.username or "", user.first_name or "", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logging.error(f"Error adding user: {e}")

    # Отправляем длинное сообщение через нашу функцию
    await send_long_message(message.chat.id, WELCOME_TEXT)


@dp.callback_query(F.data == "join_chat_info")
async def join_chat_info(callback: CallbackQuery):
    text = (
        "<b>Чтобы попасть в чат с сигналами</b>\n\n"
        "⚠️ Зарегистрируйся по моей реф-ссылке:\n"
        "👉 <a href='https://bingx.com/invite/XQ1AMO'>https://bingx.com/invite/XQ1AMO</a>\n"
        "Код: <code>XQ1AMO</code>\n\n"
        "После — отправь UID в @Gold_Denys"
    )
    await send_long_message(callback.message.chat.id, text)

@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery):
    await callback.message.answer("😈 Информация обо мне появится позже.")

@dp.callback_query(F.data == "reviews")
async def reviews_handler(callback: CallbackQuery):
    await callback.message.answer("📝 Отзывы будут добавлены позже.")

@dp.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    await callback.message.answer("📊 Статистика будет добавлена позже.")

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 Панель администратора", reply_markup=admin_kb)

@dp.message(F.text == "📈 Статистика")
async def admin_stats(message: Message):
    if message.from_user.id == ADMIN_ID:
        users = db.get_all_users()
        await message.answer(f"📊 В базе {len(users)} пользователей.")

@dp.message(F.text == "📥 Экспорт .xlsx")
async def export_excel(message: Message):
    if message.from_user.id == ADMIN_ID:
        filename = db.export_users_to_excel()
        await message.answer_document(FSInputFile(filename))

@dp.message(F.text == "📤 Рассылка")
async def start_broadcast(message: Message):
    if message.from_user.id == ADMIN_ID:
        broadcast_mode[message.from_user.id] = True
        await message.answer("✏️ Введи текст рассылки:")

@dp.message(F.text == "➕ Добавить в чат")
async def start_add_user(message: Message):
    if message.from_user.id == ADMIN_ID:
        add_mode[message.from_user.id] = True
        await message.answer("🔢 Введи Telegram ID пользователя (число):")

@dp.message()
async def fallback_handler(message: Message):
    uid = message.from_user.id
    if broadcast_mode.get(uid):
        users = db.get_all_users()
        count = 0
        for user_id in users:
            try:
                await bot.send_message(user_id, f"📢 Важно:\n\n{message.text}")
                count += 1
            except Exception:
                continue
        broadcast_mode[uid] = False
        await message.answer(f"✅ Отправлено {count} пользователям.")
    elif add_mode.get(uid):
        try:
            new_id = int(message.text)
            await bot.send_message(new_id, "✅ Вы были добавлены в чат.")
            await bot.add_chat_member(chat_id=GROUP_CHAT_ID, user_id=new_id)
            await message.answer("✅ Пользователь добавлен!")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
        add_mode[uid] = False


# Запуск бота
async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
