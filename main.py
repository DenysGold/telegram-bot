import asyncio
import logging
from datetime import datetime
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import db  # Обязательно создай файл db.py

API_TOKEN = "7920083802:AAEi4cYNYg_oEPPXDldV8corWs7HgHwQtKI"
ADMIN_ID = 911957250
GROUP_CHAT_ID = -1000000000000  # Заменить на реальный ID

# 🔹 Flask для keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот работает (Flask)!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# 🔹 Логгирование
logging.basicConfig(level=logging.INFO)

# 🔹 Инициализация
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

broadcast_mode = {}

# 🔹 Главное меню
main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔥 ПОПАСТЬ В ЧАТ С СИГНАЛАМИ", callback_data="join_chat_info")],
    [InlineKeyboardButton(text="📝 ОТЗЫВЫ", callback_data="reviews")],
    [InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="stats")],
    [InlineKeyboardButton(text="😈 ОБО МНЕ", callback_data="about")]
])

# 🔹 Клавиатура администратора
admin_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="📤 Рассылка"), KeyboardButton(text="📈 Статистика")],
        [KeyboardButton(text="📥 Экспорт .xlsx"), KeyboardButton(text="➕ Добавить в чат")]
    ]
)

# 🔹 Старт
@router.message(Command("start"))
async def start_handler(message: types.Message):
    user = message.from_user
    join_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        db.add_user(user.id, user.username or "", user.first_name or "", join_date)
    except:
        pass

    text = (
        "👋 Привет друг, здесь можно получить доступ к нашему торговому комьюнити.\n\n"
        "🔹 сигналы на сделки\n🔹 инвестиционные идеи\n🔹 обучающие уроки\n\n"
        "Для входа — зарегистрируйся на бирже BingX по ссылке:\n\n"
        "👉 <a href='https://bingx.com/invite/XQ1AMO'>https://bingx.com/invite/XQ1AMO</a>\n"
        "<b>Код: <code>XQ1AMO</code></b>\n\n"
        "После регистрации напиши @Gold_Denys и отправь свой UID — добавим в закрытый чат."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_kb, disable_web_page_preview=True)

# 🔹 Коллбэки
@router.callback_query(lambda c: c.data == "join_chat_info")
async def join_chat_info(callback_query: types.CallbackQuery):
    await callback_query.message.answer(
        "<b>Чтобы попасть в чат с сигналами</b>\n\n"
        "⚠️ Зарегистрируйся по ссылке:\n"
        "👉 <a href='https://bingx.com/invite/XQ1AMO'>https://bingx.com/invite/XQ1AMO</a>\n"
        "<b>UID пришли @Gold_Denys</b>", parse_mode="HTML", disable_web_page_preview=True
    )

@router.callback_query(lambda c: c.data == "about")
async def about(callback_query: types.CallbackQuery):
    await callback_query.message.answer("😈 Информация обо мне появится здесь позже.")

@router.callback_query(lambda c: c.data == "reviews")
async def reviews(callback_query: types.CallbackQuery):
    await callback_query.message.answer("📝 Отзывы будут добавлены позже.")

@router.callback_query(lambda c: c.data == "stats")
async def stats(callback_query: types.CallbackQuery):
    await callback_query.message.answer("📊 Статистика будет добавлена позже.")

# 🔹 Панель админа
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 Панель администратора", reply_markup=admin_kb)

# 🔹 Команды админа
@router.message(lambda m: m.text == "📈 Статистика")
async def admin_stats(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        users = db.get_all_users()
        await message.answer(f"📊 В базе {len(users)} пользователей.")

@router.message(lambda m: m.text == "📥 Экспорт .xlsx")
async def admin_export_excel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        filename = db.export_users_to_excel()
        await message.answer_document(types.FSInputFile(filename))

@router.message(lambda m: m.text == "📤 Рассылка")
async def admin_broadcast_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        broadcast_mode[message.from_user.id] = True
        await message.answer("✏️ Введи текст рассылки:")

@router.message()
async def admin_text(message: types.Message):
    if broadcast_mode.get(message.from_user.id):
        users = db.get_all_users()
        count = 0
        for uid in users:
            try:
                await bot.send_message(uid, f"📢 Сообщение:\n\n{message.text}")
                count += 1
            except:
                pass
        broadcast_mode[message.from_user.id] = False
        await message.answer(f"✅ Отправлено {count} пользователям.")

# 🔹 Запуск
async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
