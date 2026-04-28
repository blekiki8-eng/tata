from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio
import logging
import os

# ===================== НАЛАШТУВАННЯ =====================
TOKEN = os.getenv("BOT_TOKEN", "8694292932:AAHukPD-1zBf_dsFdSQCE-iam7CvvENmjJ8")
WEB_APP_URL = "https://tata-production-5086.up.railway.app"
ADMIN_ID = 1642108682

RATE = 4.45

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

pending_payments = {}

def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Games", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💰 Donate", callback_data="donate")]
    ])

# ===================== ХЕНДЛЕРИ =====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Вітаю в <b>Рибалка Віті</b>!\n\nОбери дію:",
        reply_markup=get_start_keyboard()
    )

@dp.callback_query(F.data == "donate")
async def donate_start(callback: types.CallbackQuery):
    await callback.message.edit_text("💎 Введіть кількість донат валюти (💎), яку хочете купити:")
    await callback.answer()

@dp.message(lambda m: m.text and m.text.replace(".", "", 1).replace(",", "", 1).isdigit())
async def get_amount(message: types.Message):
    try:
        diamonds = float(message.text.replace(",", "."))
        if diamonds <= 0:
            return await message.answer("Введіть число більше 0.")

        pending_payments[message.from_user.id] = diamonds
        amount_uah = round(diamonds * RATE, 2)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏦 Абанк", callback_data=f"bank_abank_{diamonds}")],
            [InlineKeyboardButton(text="🏦 ПУМБ", callback_data=f"bank_pumb_{diamonds}")]
        ])

        await message.answer(
            f"Ви хочете купити <b>{diamonds} 💎</b>\n"
            f"До сплати: <b>{amount_uah} ₴</b>\n\n"
            "Оберіть банк:",
            reply_markup=keyboard
        )
    except:
        await message.answer("Будь ласка, введіть число.")

@dp.callback_query(F.data.startswith("bank_"))
async def choose_bank(callback: types.CallbackQuery):
    _, bank, diamonds_str = callback.data.split("_")
    diamonds = float(diamonds_str)
    amount = round(diamonds * RATE, 2)

    card = "4400 0055 5011 1519" if bank == "abank" else "5355 2800 2890 2177"
    bank_name = "Абанк" if bank == "abank" else "ПУМБ"

    await callback.message.edit_text(
        f"🏦 Ви вибрали <b>{bank_name}</b>\n\n"
        f"До сплати: <b>{diamonds} 💎 = {amount} ₴</b>\n\n"
        f"Карта:\n<code>{card}</code>\n\n"
        "Після оплати скиньте квитанцію (фото) в цей чат."
    )

# Обробка фото (квитанцій)
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id not in pending_payments:
        return await message.answer("Спочатку натисніть Donate і введіть кількість 💎.")

    diamonds = pending_payments[message.from_user.id]

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"🧾 Нова квитанція!\n\n"
                f"Користувач: {message.from_user.full_name}\n"
                f"ID: {message.from_user.id}\n"
                f"💎: {diamonds}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"confirm_{message.from_user.id}_{diamonds}")],
            [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{message.from_user.id}")]
        ])
    )

    await message.answer("Квитанція відправлена на перевірку.")

# Підтвердження / Відхилення (тільки для адміна)
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm(callback: types.CallbackQuery):
    _, user_id, diamonds = callback.data.split("_")
    user_id = int(user_id)
    diamonds = float(diamonds)

    await bot.send_message(user_id, f"✅ Оплата підтверджена!\nВам нараховано <b>{diamonds} 💎</b>")
    await callback.message.edit_caption(callback.message.caption + "\n\n✅ ПІДТВЕРДЖЕНО")
    pending_payments.pop(user_id, None)

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(user_id, "❌ Оплата відхилена.\nНапишіть @vex0o0")
    await callback.message.edit_caption(callback.message.caption + "\n\n❌ ВІДХИЛЕНО")
    pending_payments.pop(user_id, None)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
