import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Налаштування
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БОТ ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Грати в Рибалку", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="💰 Донат", callback_data="donate_menu")]
    ])
    await message.answer(f"Привіт, Кака! Коко на зв'язку. Риба чекає!", reply_markup=keyboard)

# --- ВЕБ-СЕРВЕР ---
async def handle_index(request):
    # Переконайся, що файл index.html лежить в тій же папці
    return web.FileResponse('index.html')

app = web.Application()
app.router.add_get('/', handle_index)

async def main():
    # Запуск сервера
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    print(f"Сервер запущено на порту {PORT}")
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Помилка: {e}")
