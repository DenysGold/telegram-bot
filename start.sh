@dp.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    try:
        db.add_user(user.id, user.username or "", user.first_name or "", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logging.error(f"Error adding user: {e}")

    await bot.send_message(
        message.chat.id,
        WELCOME_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_kb,
        disable_web_page_preview=False  # ОБРАТИ ВНИМАНИЕ — теперь False
    )
