import os
import asyncio
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

# Виводимо логи відразу
print("Бот запускається...")

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
MONGO_URL = os.getenv("MONGO_URL")
PORT = int(os.getenv("PORT", 8080))
ADMIN_ID = 1642108682 

if not MONGO_URL:
    print("ПОМИЛКА: MONGO_URL не знайдено!")
    sys.exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Підключення до MongoDB
try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["fish_cash_game"]
    users_col = db["users"]
    print("Успішне підключення до MongoDB")
except Exception as e:
    print(f"Помилка підключення до MongoDB: {e}")

# --- API ДЛЯ ГРИ ---
async def get_balance(request):
    user_id = request.query.get("user_id")
    if not user_id: 
        return web.json_response({"error": "no_id"}, status=400)
    
    user = await users_col.find_one({"user_id": str(user_id)})
    if not user:
        user = {"user_id": str(user_id), "coins": 100, "dfc": 0, "promos": [], "name": "Рибалка"}
        await users_col.insert_one(user)
    
    user.pop("_id", None)
    return web.json_response(user)

async def save_balance(request):
    try:
        data = await request.json()
        u_id = str(data.get("user_id"))
        await users_col.update_one(
            {"user_id": u_id},
            {"$set": {
                "coins": data.get("coins"),
                "dfc": data.get("dfc"),
                "promos": data.get("promos")
            }}
        )
        return web.json_response({"status": "ok"})
    except Exception as e:
        print(f"Помилка API: {e}")
        return web.json_response({"status": "error"}, status=400)

# --- ЛОГІКА БОТА ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    full_name = message.from_user.full_name
    
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        await users_col.insert_one({
            "user_id": user_id, 
            "coins": 100, 
            "dfc": 0, 
            "promos": [], 
            "name": full_name
        })
        
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            ref_id = args[1].replace("ref_", "")
            if ref_id != user_id:
                await users_col.update_one({"user_id": ref_id}, {"$inc": {"coins": 100}})
                try:
                    await bot.send_message(ref_id, f"🎊 +100 монет! Новий реферал: {full_name}")
                except:
                    pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Грати в Fish Cash", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(f"Привіт, {full_name}! Твій баланс збережено в хмарі. 🌊", reply_markup=kb)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = await users_col.find().to_list(length=100)
    if not users:
        return await message.answer("Гравців немає.")
    
    res = "📊 **Список гравців:**\n\n"
    for u in users:
        res += f"👤 {u.get('name')}\n💰 Coins: {u['coins']} | ID: `{u['user_id']}`\n---\n"
    await message.answer(res, parse_mode="Markdown")

# --- СЕРВЕР ---
async def handle_index(request): 
    return web.FileResponse('index.html')

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/get_balance', get_balance)
app.router.add_post('/api/save_balance', save_balance)

async def main():
    print(f"Запуск на порту {PORT}...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print("HTTP Сервер готовий!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Помилка: {e}")
