import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL") 
MONGO_URL = os.getenv("MONGO_URL")
PORT = int(os.getenv("PORT", 8080))

CHANNELS = [{"url": "https://t.me/vexoo_hub", "id": "@vexoo_hub"}]

# Список промокодів
PROMO_CODES = {
    "hello": 100,
    "News": 67
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

client = AsyncIOMotorClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client["fish_cash_test_db"]
users_col = db["users"]

# --- API ДЛЯ ПРОМОКОДІВ ---
async def use_promo(request):
    try:
        data = await request.json()
        u_id = str(data.get("user_id"))
        code = data.get("code")

        if code in PROMO_CODES:
            bonus = PROMO_CODES[code]
            # Перевіряємо, чи не використовував вже (додаємо список використаних кодів користувачу)
            user = await users_col.find_one({"user_id": u_id})
            used_promos = user.get("used_promos", [])

            if code in used_promos:
                return web.json_response({"ok": False, "message": "Вже використано!"})

            await users_col.update_one(
                {"user_id": u_id},
                {
                    "$inc": {"coins": bonus},
                    "$push": {"used_promos": code}
                }
            )
            return web.json_response({"ok": True, "bonus": bonus})
        else:
            return web.json_response({"ok": False, "message": "Невірний код!"})
    except:
        return web.json_response({"ok": False}, status=500)

# --- РЕШТА ФУНКЦІЙ (БЕЗ ЗМІН) ---
async def get_balance(request):
    user_id = request.query.get("user_id")
    user = await users_col.find_one({"user_id": str(user_id)})
    if user:
        user.pop("_id", None)
        return web.json_response(user)
    return web.json_response({"error": "not_found"}, status=404)

async def save_balance(request):
    data = await request.json()
    await users_col.update_one({"user_id": str(data.get("user_id"))}, {"$set": {"coins": int(data.get("coins"))}}, upsert=True)
    return web.json_response({"ok": True})

async def handle_index(request): return web.FileResponse('index.html')
async def handle_poplavok(request): return web.FileResponse('poplavok.png')

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/get_balance', get_balance)
app.router.add_post('/api/save_balance', save_balance)
app.router.add_post('/api/use_promo', use_promo) # Новий маршрут

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
