from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import F
import asyncio
import logging

# ===================== НАЛАШТУВАННЯ =====================
TOKEN = "8694292932:AAHukPD-1zBf_dsFdSQCE-iam7CvvENmjJ8"
WEB_APP_URL = "https://tata-production-5086.up.railway.app"

# Курс
DIAMOND_TO_USD = 4.45
USD_TO_UAH = 44.50

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ===================== КЛАВІАТУРА =====================
def get_start_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Games", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💰 Donate", callback_data="donate")]
    ])
    return keyboard

def get_bank_keyboard(diamonds: int):
    amount_uah = round(diamonds * DIAMOND_TO_USD * USD_TO_UAH, 2)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 Абанк", callback_data=f"bank_abank_{diamonds}")],
        [InlineKeyboardButton(text="🏦 ПУМБ", callback_data=f"bank_pumb_{diamonds}")]
    ])
    return keyboard, amount_uah

# ===================== ХЕНДЛЕРИ =====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Вітаю в <b>Рибалка Віті</b>!\n\n"
        "Обери, що хочеш зробити:",
        reply_markup=get_start_keyboard()
    )

@dp.callback_query(F.data == "donate")
async def donate_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💎 <b>Поповнення донат валюти</b>\n\n"
        "Напишіть, яку кількість донат валюти (в 💎) ви хочете придбати:"
    )
    await callback.answer()

# Обробка введеної кількості діамантів
@dp.message(lambda message: message.text and message.text.replace('.', '', 1).replace(',', '', 1).isdigit())
async def process_diamond_amount(message: types.Message):
    try:
        diamonds = float(message.text.replace(',', '.'))
        if diamonds <= 0:
            await message.answer("❌ Будь ласка, введіть число більше 0.")
            return
        
        keyboard, amount_uah = get_bank_keyboard(diamonds)
        
        await message.answer(
            f"✅ Ви хочете придбати <b>{diamonds} 💎</b>\n\n"
            f"До сплати: <b>{amount_uah} ₴</b> (курс 1💎 = {DIAMOND_TO_USD}$ × {USD_TO_UAH}₴)\n\n"
            "Оберіть банк для оплати:",
            reply_markup=keyboard
        )
    except:
        await message.answer("❌ Будь ласка, введіть число.")

# Обробка вибору банку
@dp.callback_query(F.data.startswith("bank_"))
async def process_bank(callback: types.CallbackQuery):
    _, bank, diamonds_str = callback.data.split("_")
    diamonds = float(diamonds_str)
    amount_uah = round(diamonds * DIAMOND_TO_USD * USD_TO_UAH, 2)

    if bank == "abank":
        card = "4400 0055 5011 1519"
        bank_name = "Абанк"
    else:
        card = "5355 2800 2890 2177"
        bank_name = "ПУМБ"

    text = (
        f"🏦 <b>Ви вибрали {bank_name}</b>\n\n"
        f"До сплати: <b>{diamonds} 💎 = {amount_uah} ₴</b>\n"
        f"(1💎 = {DIAMOND_TO_USD}$ × {USD_TO_UAH}₴)\n\n"
        f"Номер карти:\n<code>{card}</code>\n\n"
        "⚠️ <b>Після оплати обов’язково скиньте квитанцію сюди!</b>"
    )

    await callback.message.edit_text(text)
    await callback.answer()

# ===================== ЗАПУСК =====================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот успішно запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
