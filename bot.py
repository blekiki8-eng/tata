import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Налаштування
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЛОГІКА БОТА ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    # Твій новий текст привітання
    text = "Вітаю Fish Cash на базі! Рибка вже ловиться 🎣"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎣 Грати в Рибалку", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Донат", 
                callback_data="donate_menu"
            )
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard)

# Обробка кнопки Донат
@dp.callback_query(F.data == "donate_menu")
async def donate_callback(callback: types.CallbackQuery):
    await callback.message.answer("Розділ Донат (DFC) буде доступний незабаром! Слідкуйте за оновленнями. 💎")
    await callback.answer()

# --- ВЕБ-СЕРВЕР ДЛЯ ГРИ ---

async def handle_index(request):
    return web.FileResponse('index.html')

app = web.Application()
app.router.add_get('/', handle_index)

async def main():
    # Запуск веб-сервера (для Railway)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    print(f"Сервер працює на порту {PORT}")
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Помилка: {e}")nt(f"Помилка: {e}")
