from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio
import logging

# ===================== НАЛАШТУВАННЯ =====================
TOKEN = "8694292932:AAHukPD-1zBf_dsFdSQCE-iam7CvvENmjJ8"
WEB_APP_URL = "https://tata-production-5086.up.railway.app"
ADMIN_ID = 1642108682        # ← Твій ID

RATE = 4.45  # 1 💎 = 4.45 грн

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# Зберігання очікуваних платежів
pending_payments = {}

# ===================== КЛАВІАТУРА =====================
def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Games", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💰 Donate", callback_data="donate")]
    ])

def get_confirm_keyboard(user_id: int, diamonds: float):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"confirm_{user_id}_{diamonds}"),
            InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{user_id}")
        ]
    ])

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

# Обробка введеної кількості 💎
@dp.message(lambda m: m.text and m.text.replace('.', '', 1).replace(',', '', 1).isdigit())
async def process_diamond_amount(message: types.Message):
    try:
        diamonds = float(message.text.replace(',', '.'))
        if diamonds <= 0:
            return await message.answer("❌ Введіть число більше 0.")

        pending_payments[message.from_user.id] = diamonds

        await message.answer(
            f"✅ Ви хочете придбати <b>{diamonds} 💎</b>\n"
            f"Сума до сплати: <b>{round(diamonds * RATE, 2)} ₴</b>\n\n"
            "Оберіть банк для оплати:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏦 Абанк", callback_data=f"bank_abank_{diamonds}")],
                [InlineKeyboardButton(text="🏦 ПУМБ", callback_data=f"bank_pumb_{diamonds}")]
            ])
        )
    except:
        await message.answer("❌ Будь ласка, введіть число (наприклад: 10)")

# Вибір банку
@dp.callback_query(F.data.startswith("bank_"))
async def process_bank(callback: types.CallbackQuery):
    _, bank, diamonds_str = callback.data.split("_")
    diamonds = float(diamonds_str)

    if bank == "abank":
        card = "4400 0055 5011 1519"
        bank_name = "Абанк"
    else:
        card = "5355 2800 2890 2177"
        bank_name = "ПУМБ"

    await callback.message.edit_text(
        f"🏦 Ви вибрали <b>{bank_name}</b>\n\n"
        f"До сплати: <b>{diamonds} 💎 = {round(diamonds * RATE, 2)} ₴</b>\n\n"
        f"Карта:\n<code>{card}</code>\n\n"
        "Після оплати скиньте квитанцію (фото) в цей чат."
    )

# Обробка квитанцій (фото)
@dp.message(F.photo)
async def handle_receipt(message: types.Message):
    if message.from_user.id not in pending_payments:
        return await message.answer("❌ Спочатку виберіть кількість 💎 через кнопку Donate.")

    diamonds = pending_payments[message.from_user.id]
    amount = round(diamonds * RATE, 2)

    # Пересилаємо тобі (адміну) квитанцію
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"🧾 Нова квитанція на перевірку!\n\n"
                f"Користувач: <b>{message.from_user.full_name}</b>\n"
                f"Username: @{message.from_user.username or 'немає'}\n"
                f"ID: <code>{message.from_user.id}</code>\n"
                f"Кількість: <b>{diamonds} 💎</b> ({amount} ₴)",
        reply_markup=get_confirm_keyboard(message.from_user.id, diamonds)
    )

    await message.answer("✅ Квитанція відправлена адміністратору на перевірку.\nОчікуйте відповіді.")

# Підтвердження оплати
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    _, user_id_str, diamonds_str = callback.data.split("_")
    user_id = int(user_id_str)
    diamonds = float(diamonds_str)

    await bot.send_message(
        user_id,
        f"✅ <b>Оплата підтверджена!</b>\n\n"
        f"Вам нараховано <b>{diamonds} 💎</b> донат валюти."
    )

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ ПІДТВЕРДЖЕНО"
    )
    await callback.answer("Підтверджено")

    if user_id in pending_payments:
        del pending_payments[user_id]

# Відхилення оплати
@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    await bot.send_message(
        user_id,
        "❌ Оплата відхилена.\n\nБудь ласка, напишіть власнику @vex0o0"
    )

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ ВІДХИЛЕНО"
    )
    await callback.answer("Відхилено")

    if user_id in pending_payments:
        del pending_payments[user_id]

# ===================== ЗАПУСК =====================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот запущений! Очікую квитанції...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
