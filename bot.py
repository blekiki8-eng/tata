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

# ===================== ХЕНДЛЕРИ =====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Вітаю в <b>Рибалка Віті</b>!\n\nОбери дію:",
        reply_markup=get_start_keyboard()
    )

@dp.callback_query(F.data == "donate")
async def donate_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💎 Введіть кількість донат валюти (💎), яку хочете придбати:"
    )
    await callback.answer()

# ===================== ЗАПУСК =====================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот успішно запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
