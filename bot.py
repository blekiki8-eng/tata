import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# "База даних" у пам'яті (після перезавантаження Railway обнулиться, 
# але при оновленні сторінки в Telegram — баланс залишиться!)
user_data = {} 

# --- API ДЛЯ ГРИ ---
async def get_balance(request):
    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"error": "no_id"}, status=400)
    
    # Якщо юзера немає, створюємо з 100 монетами
    if user_id not in user_data:
        user_data[user_id] = {"coins": 100, "dfc": 0, "promos": []}
    
    return web.json_response(user_data[user_id])

async def save_balance(request):
    data = await request.json()
    user_id = str(data.get("user_id"))
    if user_id in user_data:
        user_data[user_id]["coins"] = data.get("coins")
        user_data[user_id]["dfc"] = data.get("dfc")
        user_data[user_id]["promos"] = data.get("promos", [])
        return web.json_response({"status": "ok"})
    return web.json_response({"status": "error"}, status=400)

# --- ЛОГІКА БОТА ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    # Логіка реферала (якщо зайшов по лінку)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = args[1].replace("ref_", "")
        if referrer_id != str(message.from_user.id):
            # Тут можна додати логіку нарахування бонусу рефереру
            pass

    text = "Вітаю Fish Cash на базі! Рибка вже ловиться 🎣"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Грати в Рибалку", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="💰 Донат", callback_data="donate_menu")]
    ])
    await message.answer(text, reply_markup=keyboard)

# --- НАЛАШТУВАННЯ СЕРВЕРА ---
app = web.Application()
# Роздаємо HTML
app.router.add_get('/', lambda r: web.FileResponse('index.html'))
# API точки
app.router.add_get('/api/get_balance', get_balance)
app.router.add_post('/api/save_balance', save_balance)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
