import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

# --- Конфігурація з Railway Variables ---
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
MONGO_URL = os.getenv("MONGO_URL")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Підключення до MongoDB Atlas ---
client = AsyncIOMotorClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client["fish_cash_game_prod"]
users_col = db["users"]

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    # Покращена логіка отримання імені
    full_name = message.from_user.full_name or message.from_user.username or "Гравець"
    
    # Обробка реферального посилання
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None

    user = await users_col.find_one({"user_id": user_id})
    if not user:
        # Створення нового профілю (100 монет старт)
        await users_col.insert_one({
            "user_id": user_id, 
            "coins": 100, 
            "name": full_name
        })
        
        # Нарахування бонусу тому, хто запросив
        if referrer_id and referrer_id != user_id:
            await users_col.update_one({"user_id": referrer_id}, {"$inc": {"coins": 50}})
            try:
                await bot.send_message(referrer_id, f"💎 Твій друг {full_name} приєднався! Тобі нараховано +50 монет!")
            except: 
                pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Грати в Fish Cash", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    welcome_text = f"Привіт, {full_name}! 🌊\nГотовий наловити на ламборгіні?\n\nТвій ID: {user_id}"
    
    # Спроба відправити фото welcome.jpg, якщо воно є в репозиторії
    try:
        photo = FSInputFile("welcome.jpg")
        await message.answer_photo(photo=photo, caption=welcome_text, reply_markup=kb)
    except Exception:
        await message.answer(welcome_text, reply_markup=kb)

# --- API СЕРВЕР ДЛЯ ГРИ ---

async def get_balance(request):
    """Отримання даних гравця для WebApp"""
    user_id = request.query.get("user_id")
    user = await users_col.find_one({"user_id": str(user_id)})
    if user:
        user.pop("_id", None)  # Видаляємо службовий ID бази
        return web.json_response(user)
    return web.json_response({"error": "not_found"}, status=404)

async def save_balance(request):
    """Збереження балансу після вилову"""
    try:
        data = await request.json()
        await users_col.update_one(
            {"user_id": str(data.get("user_id"))}, 
            {"$set": {"coins": int(data.get("coins"))}}, 
            upsert=True
        )
        return web.json_response({"ok": True})
    except Exception:
        return web.json_response({"ok": False}, status=500)

# --- МАРШРУТИ ДЛЯ ФАЙЛІВ ---
async def handle_index(request): 
    return web.FileResponse('index.html')

async def handle_poplavok(request): 
    return web.FileResponse('poplavok.png')

# --- ЗАПУСК ДОДАТКУ ---
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/poplavok.png', handle_poplavok)
app.router.add_get('/api/get_balance', get_balance)
app.router.add_post('/api/save_balance', save_balance)

async def main():
    # Запуск веб-сервера на порту Railway
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    # Запуск бота (Polling)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
