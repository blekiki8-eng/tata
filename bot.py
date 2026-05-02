import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

# --- НАЛАШТУВАННЯ ---
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL") 
MONGO_URL = os.getenv("MONGO_URL")
PORT = int(os.getenv("PORT", 8080))

# ТЕПЕР ТУТ ТІЛЬКИ ОДИН КАНАЛ
CHANNELS = [
    {"url": "https://t.me/vexoo_hub", "id": "@vexoo_hub"}
]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# MongoDB
client = AsyncIOMotorClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client["fish_cash_game_prod"]
users_col = db["users"]

# --- ФУНКЦІЯ ПЕРЕВІРКИ ПІДПИСКИ ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"ПОМИЛКА ПЕРЕВІРКИ: {e}")
            return False
    return True

# --- ОБРОБНИК КОМАНДИ /START ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Підписатися на Vexoo Hub", url=CHANNELS[0]["url"])],
            [InlineKeyboardButton(text="✅ Я підписався", callback_data="check_sub")]
        ])
        await message.answer(
            "👋 Привіт! Щоб грати, підпишись на наш канал:",
            reply_markup=kb
        )
        return

    await show_main_menu(message)

# --- ОБРОБНИК КНОПКИ ПЕРЕВІРКИ ---
@dp.callback_query(lambda c: c.data == "check_sub")
async def process_check_sub(callback: types.CallbackQuery):
    is_subscribed = await check_subscription(callback.from_user.id)
    
    if is_subscribed:
        await callback.answer("Доступ відкрито! 🎉")
        await callback.message.delete()
        await show_main_menu(callback.message)
    else:
        await callback.answer("Ти ще не підписався! ❌", show_alert=True)

async def show_main_menu(message: types.Message):
    u_id = str(message.chat.id)
    full_name = message.chat.full_name or "Гравець"
    
    user = await users_col.find_one({"user_id": u_id})
    if not user:
        await users_col.insert_one({"user_id": u_id, "coins": 100, "name": full_name})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Грати в Fish Cash", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="♟️ Грати в Шахи", web_app=WebAppInfo(url=f"{WEBAPP_URL}/chess.html"))]
    ])
    
    text = f"Привіт, {full_name}! 👋\nОбирай гру:"
    await bot.send_message(message.chat.id, text, reply_markup=kb)

# --- API ---
async def get_balance(request):
    user_id = request.query.get("user_id")
    user = await users_col.find_one({"user_id": str(user_id)})
    if user:
        user.pop("_id", None)
        return web.json_response(user)
    return web.json_response({"error": "not_found"}, status=404)

async def save_balance(request):
    try:
        data = await request.json()
        await users_col.update_one(
            {"user_id": str(data.get("user_id"))}, 
            {"$set": {"coins": int(data.get("coins"))}}, 
            upsert=True
        )
        return web.json_response({"ok": True})
    except:
        return web.json_response({"ok": False}, status=500)

async def handle_index(request): return web.FileResponse('index.html')
async def handle_chess(request): return web.FileResponse('chess.html')
async def handle_poplavok(request): return web.FileResponse('poplavok.png')

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/chess.html', handle_chess)
app.router.add_get('/poplavok.png', handle_poplavok)
app.router.add_get('/api/get_balance', get_balance)
app.router.add_post('/api/save_balance', save_balance)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
