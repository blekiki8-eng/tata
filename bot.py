import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Токен беремо з перемінних середовища Railway
TOKEN = os.getenv("BOT_TOKEN")
# Сюди встав посилання на твій сайт/сторінку з грою
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-game-url.com") 

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    # Створюємо дві кнопки, як ти і просив
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            # Кнопка 1: Веб-ап ігра
            InlineKeyboardButton(
                text="🎣 Грати в Рибалку", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            # Кнопка 2: Донат
            InlineKeyboardButton(
                text="💰 Донат", 
                callback_data="donate_menu"
            )
        ]
    ])
    
    await message.answer(
        f"Привіт, Кака! Я твій помічник Коко. 🥥\n\nОбирай, що робитимемо:",
        reply_markup=keyboard
    )

# Обробник натискання на кнопку Донат
@dp.callback_query(F.data == "donate_menu")
async def donate_process(callback: types.CallbackQuery):
    await callback.message.answer("Ти натиснув 'Донат'. Тут ми пізніше налаштуємо оплату (через Mono, Crypto або зірки Telegram).")
    await callback.answer() # Прибирає годинник з кнопки

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот вимкнений")
