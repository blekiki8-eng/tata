import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
MONGO_URL = os.getenv("MONGO_URL")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

client = AsyncIOMotorClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client["fish_cash_game"]
users_col = db["users"]

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    full_name = message.from_user.full_name
    
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        await users_col.insert_one({"user_id": user_id, "coins": 100, "dfc": 0, "promos": [], "name": full_name})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Грати в ОЗЕРО", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    welcome_text = "Welcome 🤗\nНегайно заходи в гру і злови більше риб!"
    
    # Відправка фото (переконайтеся, що файл welcome.jpg лежить поруч з bot.py)
    try:
        photo = FSInputFile("welcome.jpg")
        await message.answer_photo(photo=photo, caption=welcome_text, reply_markup=kb)
    except:
        # Якщо фото не знайдено, відправить просто текст
        await message.answer(welcome_text, reply_markup=kb)

# --- API ТА СЕРВЕР (БЕЗ ЗМІН) ---
async def get_balance(request):
    user_id = request.query.get("user_id")
    user = await users_col.find_one({"user_id": str(user_id)})
    if user: user.pop("_id", None)
    return web.json_response(user)

async def save_balance(request):
    data = await request.json()
    await users_col.update_one({"user_id": str(data.get("user_id"))}, {"$set": data})
    return web.json_response({"ok": True})

async def handle_index(request): return web.FileResponse('index.html')

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/get_balance', get_balance)
app.router.add_post('/api/save_balance', save_balance)

async def main():
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
