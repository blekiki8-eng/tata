import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Налаштування
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
PORT = int(os.getenv("PORT", 8080))
ADMIN_ID = 1642108682  # Твій ID зафіксовано!

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- РОБОТА З БАЗОЮ ДАНИХ (ФАЙЛ) ---
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Завантажуємо дані при старті
user_data = load_db()

# --- API ДЛЯ ГРИ ---
async def get_balance(request):
    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"error": "no_id"}, status=400)
    
    if user_id not in user_data:
        user_data[user_id] = {"coins": 100, "dfc": 0, "promos": [], "name": "Гравець"}
        save_db(user_data)
    
    return web.json_response(user_data[user_id])

async def save_balance(request):
    try:
        data = await request.json()
        u_id = str(data.get("user_id"))
        if u_id in user_data:
            user_data[u_id]["coins"] = data.get("coins")
            user_data[u_id]["dfc"] = data.get("dfc")
            user_data[u_id]["promos"] = data.get("promos", [])
            save_db(user_data) # Зберігаємо у файл при кожній зміні
        return web.json_response({"status": "ok"})
    except:
        return web.json_response({"status": "error"}, status=400)

# --- ЛОГІКА БОТА ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    full_name = message.from_user.full_name
    
    # Якщо новий гравець
    if user_id not in user_data:
        user_data[user_id] = {"coins": 100, "dfc": 0, "promos": [], "name": full_name}
        
        # Реферальний бонус
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            referrer_id = args[1].replace("ref_", "")
            if referrer_id in user_data and referrer_id != user_id:
                user_data[referrer_id]["coins"] += 100
                save_db(user_data)
                try:
                    await bot.send_message(referrer_id, f"🎉 У вас новий реферал {full_name}! Вам нараховано +100 Fish Coins!")
                except: pass
        
        save_db(user_data)

    text = f"Привіт, {full_name}! Ласкаво просимо до Fish Cash! 🎣\nТвій баланс збережено."
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 Почати Рибалку", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(text, reply_markup=keyboard)

# Команда для тебе
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return 

    if not user_data:
        await message.answer("База даних порожня.")
        return

    msg = "📊 **Список всіх рибалок:**\n\n"
    for uid, data in user_data.items():
        msg += f"👤 {data.get('name', 'Unknown')}\nID: `{uid}`\n💰 Coins: {data['coins']} | 💎 DFC: {data['dfc']}\n\n"
    
    # Якщо текст занадто довгий, Телеграм може видати помилку, тому розбиваємо (про всяк випадок)
    if len(msg) > 4096:
        await message.answer("Список занадто великий для одного повідомлення.")
    else:
        await message.answer(msg, parse_mode="Markdown")

# --- ЗАПУСК ---
async def handle_index(request):
    return web.FileResponse('index.html')

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/get_balance', get_balance)
app.router.add_post('/api/save_balance', save_balance)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Server started on port {PORT}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
