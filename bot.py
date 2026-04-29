import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Токен візьми у @BotFather і додай в налаштування Railway
TOKEN = os.getenv("BOT_TOKEN")
# Посилання на твою гру (коли задеплоїш фронтенд)
WEBAPP_URL = os.getenv("WEBAPP_URL") 

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    # Створюємо клавіатуру
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка для гри (Web App)
    game_button = InlineKeyboardButton(
        text="🎣 Почати рибалку", 
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    # Кнопка для донату
    donate_button = InlineKeyboardButton(
        text="💰 Донат", 
        callback_data="donate_clicked"
    )
    
    keyboard.add(game_button, donate_button)
    
    await message.answer(
        f"Привіт, {message.from_user.first_name}! Готовий закинути вудку?",
        reply_markup=keyboard
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
