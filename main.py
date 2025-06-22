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

from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from flask import Flask
import db  # твоя база данных, как и было

# --- Конфигурация из .env ---
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- Инициализация бота и диспетчера ---
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- Flask keep-alive для Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот работает (Flask)!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

# --- Клавиатуры ---
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

# --- Приветственное сообщение ---
WELCOME_TEXT = (
    "👋 Привет друг, ... (сокращено для примера)")

# --- Длинное сообщение с кнопками ---
async def send_long_message(chat_id: int, text: str, reply_markup=None, disable_web_page_preview=True):
    MAX_LENGTH = 4000
    start = 0
    while start < len(text):
        end = min(start + MAX_LENGTH, len(text))
        if end < len(text):
            last_newline = text.rfind('\n', start, end)
            if last_newline > start:
                end = last_newline + 1
        part = text[start:end].strip()
        if part:
            await bot.send_message(
                chat_id,
                part,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup if start == 0 else None
            )
        start = end

# --- Хендлер /start ---
@dp.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    try:
        db.add_user(user.id, user.username or "", user.first_name or "", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logging.error(f"DB error: {e}")

    await send_long_message(message.chat.id, WELCOME_TEXT, reply_markup=main_kb, disable_web_page_preview=True)

# --- Callback хендлеры ---
@dp.callback_query(F.data == "join_chat_info")
async def join_chat_info(callback: CallbackQuery):
    await send_long_message(callback.message.chat.id, "<b>Чтобы попасть в чат...</b>", disable_web_page_preview=True)

@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery):
    await callback.message.answer("😈 Информация обо мне появится позже.")

@dp.callback_query(F.data == "reviews")
async def reviews_handler(callback: CallbackQuery):
    await callback.message.answer("📝 Отзывы будут добавлены позже.")

@dp.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    await callback.message.answer("📊 Статистика будет добавлена позже.")

# --- Админ-команды ---
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠️ Панель администратора", reply_markup=admin_kb)

@dp.message(F.text == "📈 Статистика")
async def admin_stats(message: Message):
    if message.from_user.id == ADMIN_ID:
        users = db.get_all_users()
        await message.answer(f"📊 В базе {len(users)} пользователей.")

# --- Webhook конфигурация ---
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

# --- Основной запуск ---
async def main():
    keep_alive()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    asyncio.run(main())
