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
PROMO_CODES = {"hello": 100, "News": 67}
REF_BONUS = 50

bot = Bot(token=TOKEN)
dp = Dispatcher()

client = AsyncIOMotorClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client["fish_cash_final"]
users_col = db["users"]
market_col = db["market"]

async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
            if member.status in ["member", "administrator", "creator"]: return True
        except: return False
    return False

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    u_id = str(message.from_user.id)
    args = message.text.split()
    referrer = args[1] if len(args) > 1 else None

    user = await users_col.find_one({"user_id": u_id})
    if not user:
        await users_col.insert_one({
            "user_id": u_id, "coins": 100, "lang": "en",
            "name": message.from_user.full_name or "Fisherman",
            "used_promos": [], "inventory": [], "referrals": 0
        })
        if referrer and referrer != u_id:
            await users_col.update_one({"user_id": referrer}, {"$inc": {"coins": REF_BONUS, "referrals": 1}})

    if not await check_subscription(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Subscribe", url=CHANNELS[0]["url"])],
            [InlineKeyboardButton(text="✅ Check Subscription", callback_data="check_sub")]
        ])
        await message.answer("🌊 Please subscribe to enter the game:", reply_markup=kb)
        return
    
    # Оновлений текст привітання за твоїм запитом
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Play Game", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer("Welcome! Let's go fishing as soon as possible!", reply_markup=kb)

# --- API ---
async def save_user_data(request):
    data = await request.json()
    u_id = str(data.get("user_id"))
    update_data = {}
    if "coins" in data: update_data["coins"] = int(data["coins"])
    if "lang" in data: update_data["lang"] = data["lang"]
    await users_col.update_one({"user_id": u_id}, {"$set": update_data}, upsert=True)
    return web.json_response({"ok": True})

# Решта API (get_user, list_item, buy_item, use_promo) залишаються без змін...
# (Додай їх з попереднього коду)

async def handle_index(request): return web.FileResponse('index.html')
async def handle_poplavok(request): return web.FileResponse('poplavok.png')

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/poplavok.png', handle_poplavok)
app.router.add_get('/api/get_user', lambda r: get_user_data(r)) # Потрібно додати функцію
app.router.add_post('/api/save_user', save_user_data)
# Додай решту маршрутів тут...

async def main():
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    await dp.start_polling(bot)

if __name__ == '__main__': asyncio.run(main())
