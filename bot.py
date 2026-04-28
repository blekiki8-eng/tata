from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio
import logging

# ===================== НАЛАШТУВАННЯ =====================
TOKEN = "8694292932:AAHukPD-1zBf_dsFdSQCE-iam7CvvENmjJ8"
WEB_APP_URL = "https://tata-production-5086.up.railway.app"   # ← Переконайся, що це актуальне посилання!

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ===================== КЛАВІАТУРА =====================
def get_start_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎮 Games",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Donate",
                callback_data="donate"
            )
        ]
    ])
    return keyboard

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
        "Напишіть кількість 💎, яку хочете придбати:"
    )
    await callback.answer()

# Обробка кількості 💎
@dp.message(lambda m: m.text and m.text.replace('.', '', 1).replace(',', '', 1).isdigit())
async def process_amount(message: types.Message):
    try:
        diamonds = float(message.text.replace(',', '.'))
        if diamonds <= 0:
            return await message.answer("❌ Введіть число більше 0.")

        amount = round(diamonds * 4.45, 2)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏦 Абанк", callback_data=f"bank_abank_{diamonds}")],
            [InlineKeyboardButton(text="🏦 ПУМБ", callback_data=f"bank_pumb_{diamonds}")]
        ])

        await message.answer(
            f"✅ Ви хочете <b>{diamonds} 💎</b>\n"
            f"До сплати: <b>{amount} ₴</b>\n\n"
            "Оберіть банк:",
            reply_markup=keyboard
        )
    except:
        await message.answer("❌ Введіть число.")

# Решта коду з банками і квитанціями (можеш залишити як було раніше)
# ... (якщо потрібно, я додам повний код пізніше)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
