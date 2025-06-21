import asyncio
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from flask import Flask
from threading import Thread

import db  # твоя база данных с функциями add_user, get_all_users, export_users_to_excel

# 🔐 Загрузка конфигурации из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))

# ⚙️ Flask для keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот работает (Flask)!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 🔧 Логирование
logging.basicConfig(level=logging.INFO)

# 🤖 Инициализация бота и диспетчера с ботом!
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
router = Router()
dp.include_router(router)

# Состояние рассылки и добавления UID
broadcast_mode = {}

# Главное меню
main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔥 ПОПАСТЬ В ЧАТ С СИГНАЛАМИ", callback_data="join_chat_info")],
    [InlineKeyboardButton(text="📝 ОТЗЫВЫ", callback_data="reviews")],
    [InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="stats")],
    [InlineKeyboardButton(text="😈 ОБО МНЕ", callback_data="about")]
])

# Клавиатура админа
admin_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="📤 Рассылка"), KeyboardButton(text="📈 Статистика")],
    [KeyboardButton(text="📥 Экспорт .xlsx"), KeyboardButton(text="➕ Добавить в чат")]
])

@router.message(Command("start"))
async def start_handler(message: types.Message):
    user = message.from_user
    join_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        db.add_user(user.id, user.username or "", user.first_name or "", join_date)
    except Exception as e:
        logging.error(f"DB add_user error: {e}")

    text = (
        "👋 Привет друг, здесь можно получить доступ к нашему торговому комьюнити.\n\n"
        "Здесь тебя ждут:\n"
        "🔹 сигналы на сделки\n"
        "🔹 инвестиционные идеи\n"
        "🔹 обучающие уроки\n\n"
        "Для того, чтобы попасть в него, тебе необходимо зарегистрироваться на бирже BingX и пополнить баланс.\n\n"
        "<b>Для удобства прикрепляю инструкции:</b>\n\n"
        "📘 <a href='https://telegra.ph/Kak-zaregistrirovatsya-na-kripto-birzhe-BingX-06-13'>КАК ЗАРЕГИСТРИРОВАТЬСЯ НА БИРЖЕ BingX</a>\n"
        "📘 <a href='https://telegra.ph/Instrukciya-po-perenosu-KYC-06-13'>ПОШАГОВАЯ ИНСТРУКЦИЯ ПЕРЕНОСА ВЕРИФИКАЦИИ</a>\n"
        "📘 <a href='https://telegra.ph/Kak-kupit-kriptovalyutu-na-birzhe-BingX-06-13'>КАК КУПИТЬ КРИПТОВАЛЮТУ ЧЕРЕЗ P2P</a>\n"
        "📘 <a href='https://telegra.ph/Rabota-so-sdelkami-na-BingX-06-13'>РАБОТА СО СДЕЛКАМИ НА BingX</a>\n"
        "📘 <a href='https://telegra.ph/Otkrytie-sdelki-LONG-i-SHORT-06-14'>ОТКРЫТИЕ LONG/SHORT СДЕЛОК</a>\n\n"
        "Если у тебя уже есть аккаунт на BingX — ты можешь <b>перенести его под мою ссылку</b>. Это несложно и займет 15 минут.\n\n"
        "Вопросы — пиши: @Gold_Denys"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_kb, disable_web_page_preview=True)

@router.callback_query(lambda c: c.data == "join_chat_info")
async def join_chat_info(callback_query: types.CallbackQuery):
    text = (
        "<b>Чтобы попасть в чат с сигналами</b>\n"
        "Есть одно условие —\n\n"
        "⚠️ <b>БЫТЬ ЗАРЕГИСТРИРОВАННЫМ ПО МОЕЙ РЕФЕРАЛЬНОЙ ССЫЛКЕ</b>\n\n"
        "👉 <a href='https://bingx.com/invite/XQ1AMO'>https://bingx.com/invite/XQ1AMO</a>\n\n"
        "<b>Код: <code>XQ1AMO</code></b>\n\n"
        "После регистрации по ссылке отправь <b>твой UID</b> нашему техническому специалисту: @Gold_Denys\n\n"
        "После проверки ты сразу будешь добавлен в закрытый чат с сигналами 🔥"
    )
    await callback_query.message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@router.callback_query(lambda c: c.data == "about")
async def about_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("😈 Информация обо мне появится здесь позже.")

@router.callback_query(lambda c: c.data == "reviews")
async def reviews_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("📝 Отзывы будут добавлены позже.")

@router.callback_query(lambda c: c.data == "stats")
async def stats_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("📊 Статистика будет добавлена позже.")

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 Панель администратора", reply_markup=admin_kb)

@router.message(lambda m: m.text == "📈 Статистика")
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = db.get_all_users()
    await message.answer(f"📊 В базе {len(users)} пользователей.")

@router.message(lambda m: m.text == "📥 Экспорт .xlsx")
async def admin_export_excel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    filename = db.export_users_to_excel()
    await message.answer_document(types.FSInputFile(filename))

@router.message(lambda m: m.text == "📤 Рассылка")
async def admin_broadcast_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    broadcast_mode[message.from_user.id] = True
    await message.answer("✏️ Введи текст рассылки:")

@router.message(lambda m: m.text == "➕ Добавить в чат")
async def manual_add_to_chat(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    broadcast_mode["add_uid"] = True
    await message.answer("🔢 Введи Telegram ID пользователя (число):")

@router.message()
async def general_handler(message: types.Message):
    user_id = message.from_user.id

    if broadcast_mode.get(user_id):
        users = db.get_all_users()
        count = 0
        for uid in users:
            try:
                await bot.send_message(uid, f"📢 Важно!:\n\n{message.text}")
                await asyncio.sleep(0.05)  # Антифлуд
                count += 1
            except Exception as e:
                logging.error(f"Failed to send to {uid}: {e}")
        broadcast_mode[user_id] = False
        await message.answer(f"✅ Рассылка отправлена {count} пользователям.")
        return

    if broadcast_mode.get("add_uid") and user_id == ADMIN_ID:
        try:
            uid = int(message.text)
            invite_link = await bot.export_chat_invite_link(GROUP_CHAT_ID)
            await bot.send_message(uid, f"✅ Вы были приглашены в чат по ссылке:\n{invite_link}")
            await message.answer("✅ Приглашение отправлено пользователю!")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
        broadcast_mode["add_uid"] = False
        return

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
