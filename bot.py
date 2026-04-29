import os
import asyncio
from aiogram import Bot, Dispatcher, types
from motor.motor_asyncio import AsyncIOMotorClient # Бібліотека для бази
from aiohttp import web

# Налаштування
TOKEN = os.getenv("BOT_TOKEN")
# Сюди вставляєш посилання з MongoDB Atlas (або в перемінні Railway)
MONGO_URL = os.getenv("MONGO_URL") 
ADMIN_ID = 1642108682

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Підключення до бази даних
client = AsyncIOMotorClient(MONGO_URL)
db = client["fish_cash_db"]
users_collection = db["users"]

# --- API ДЛЯ ГРИ ---
async def get_balance(request):
    user_id = request.query.get("user_id")
    if not user_id: return web.json_response({"status": "error"}, status=400)
    
    # Шукаємо юзера в хмарі
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        user = {"user_id": user_id, "coins": 100, "dfc": 0, "promos": [], "name": "Гравець"}
        await users_collection.insert_one(user)
    
    # Видаляємо службовий _id від MongoDB перед відправкою
    user.pop("_id", None)
    return web.json_response(user)

async def save_balance(request):
    data = await request.json()
    u_id = str(data.get("user_id"))
    await users_collection.update_one(
        {"user_id": u_id},
        {"$set": {
            "coins": data.get("coins"),
            "dfc": data.get("dfc"),
            "promos": data.get("promos")
        }}
    )
    return web.json_response({"status": "ok"})

# Решту логіки бота (CommandStart, admin) просто адаптуємо під await users_collection...
