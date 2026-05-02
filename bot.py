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
REF_BONUS = 50 # Бонус за друга

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
            if member.status in ["member", "administrator", "creator"]:
                return True
        except Exception: return False
    return False

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    u_id = str(message.from_user.id)
    args = message.text.split()
    referrer = args[1] if len(args) > 1 else None

    user = await users_col.find_one({"user_id": u_id})
    if not user:
        new_user = {
            "user_id": u_id, 
            "coins": 100, 
            "lang": "en",
            "name": message.from_user.full_name or "Fisherman",
            "used_promos": [],
            "inventory": [],
            "referrals": 0
        }
        await users_col.insert_one(new_user)
        # Якщо прийшов за реф-посиланням
        if referrer and referrer != u_id:
            await users_col.update_one({"user_id": referrer}, {"$inc": {"coins": REF_BONUS, "referrals": 1}})
            try: await bot.send_message(referrer, f"🎁 Someone joined by your link! You got +{REF_BONUS} coins.")
            except: pass

    if not await check_subscription(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Subscribe", url=CHANNELS[0]["url"])],
            [InlineKeyboardButton(text="✅ Check Subscription", callback_data="check_sub")]
        ])
        await message.answer("🌊 Please subscribe to enter the game:", reply_markup=kb)
        return
    await show_main_menu(message)

@dp.callback_query(lambda c: c.data == "check_sub")
async def process_check_sub(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        await show_main_menu(callback.message)
    else:
        await callback.answer("❌ Not subscribed!", show_alert=True)

async def show_main_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Play Huipizfksn Game", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await bot.send_message(message.chat.id, f"Welcome, Fisherman! Your ID: {message.chat.id}", reply_markup=kb)

# --- API ---

async def get_user_data(request):
    user_id = request.query.get("user_id")
    user = await users_col.find_one({"user_id": str(user_id)})
    if user: user.pop("_id", None)
    return web.json_response(user if user else {"error": "not_found"})

async def save_user_data(request):
    data = await request.json()
    u_id = str(data.get("user_id"))
    update_data = {}
    if "coins" in data: update_data["coins"] = int(data["coins"])
    if "lang" in data: update_data["lang"] = data["lang"]
    await users_col.update_one({"user_id": u_id}, {"$set": update_data}, upsert=True)
    return web.json_response({"ok": True})

async def list_on_market(request):
    data = await request.json()
    u_id, item_id, price = str(data.get("user_id")), data.get("item_id"), int(data.get("price"))
    user = await users_col.find_one({"user_id": u_id})
    inv = user.get("inventory", [])
    item_to_sell = next((i for i in inv if i["id"] == item_id), None)
    if item_to_sell:
        inv.remove(item_to_sell)
        await users_col.update_one({"user_id": u_id}, {"$set": {"inventory": inv}})
        await market_col.insert_one({
            "seller_id": u_id,
            "seller_name": user.get("name", "Fisherman"),
            "item_id": item_id,
            "price": price
        })
        return web.json_response({"ok": True})
    return web.json_response({"ok": False})

async def get_market(request):
    cursor = market_col.find({})
    lots = await cursor.to_list(length=50)
    for l in lots: l.pop("_id", None)
    return web.json_response(lots)

async def buy_from_market(request):
    data = await request.json()
    buyer_id, lot = str(data.get("user_id")), data.get("lot")
    buyer = await users_col.find_one({"user_id": buyer_id})
    if buyer["coins"] < lot["price"]: return web.json_response({"ok": False, "msg": "No coins"})
    res = await market_col.delete_one({"seller_id": lot["seller_id"], "item_id": lot["item_id"], "price": lot["price"]})
    if res.deleted_count > 0:
        await users_col.update_one({"user_id": buyer_id}, {"$inc": {"coins": -lot["price"]}, "$push": {"inventory": {"id": lot["item_id"]}}})
        await users_col.update_one({"user_id": lot["seller_id"]}, {"$inc": {"coins": lot["price"]}})
        return web.json_response({"ok": True})
    return web.json_response({"ok": False, "msg": "Already sold"})

async def use_promo(request):
    data = await request.json()
    u_id, code = str(data.get("user_id")), data.get("code")
    if code in PROMO_CODES:
        user = await users_col.find_one({"user_id": u_id})
        if code in user.get("used_promos", []): return web.json_response({"ok": False, "msg": "Used!"})
        await users_col.update_one({"user_id": u_id}, {"$inc": {"coins": PROMO_CODES[code]}, "$push": {"used_promos": code}})
        return web.json_response({"ok": True, "bonus": PROMO_CODES[code]})
    return web.json_response({"ok": False, "msg": "Invalid!"})

async def handle_index(request): return web.FileResponse('index.html')
async def handle_poplavok(request): return web.FileResponse('poplavok.png')

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/poplavok.png', handle_poplavok)
app.router.add_get('/api/get_user', get_user_data)
app.router.add_post('/api/save_user', save_user_data)
app.router.add_post('/api/list_item', list_on_market)
app.router.add_get('/api/get_market', get_market)
app.router.add_post('/api/buy_item', buy_from_market)
app.router.add_post('/api/use_promo', use_promo)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
