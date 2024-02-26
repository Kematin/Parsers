import asyncio
import logging
import sys
from os import environ, remove

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile
from dotenv import load_dotenv

import service

load_dotenv()

token = environ.get("TOKEN")
dp = Dispatcher()
bot = Bot(token, parse_mode=ParseMode.HTML)


async def get_city_handler(message: Message, store_id: str):
    message_delete = await message.answer("Ожидайте...")
    filename = await service.main_service(store_id=store_id)
    await bot.send_document(
        message.from_user.id,
        document=FSInputFile(path=f"./{filename}", filename=filename),
    )
    remove(f"./{filename}")
    await bot.delete_message(message.chat.id, message_delete.message_id)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    moscow_btn = types.KeyboardButton(text="Москва")
    surgut_btn = types.KeyboardButton(text="Сургут")
    peterburg_btn = types.KeyboardButton(text="Питер")
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[moscow_btn, peterburg_btn, surgut_btn]],
        resize_keyboard=True,
        input_field_placeholder="Город",
    )
    await message.answer("Отправь название города", reply_markup=keyboard)


@dp.message(F.text.lower() == "москва")
async def get_moscow(message: Message):
    await get_city_handler(message, "31Z6")


@dp.message(F.text.lower() == "сургут")
async def get_surgut(message: Message):
    await get_city_handler(message, "Q834")


@dp.message(F.text.lower() == "питер")
async def get_peterburg(message: Message):
    await get_city_handler(message, "5610")


@dp.message()
async def echo_handler(message: types.Message) -> None:
    try:
        await message.answer("Такого города в базе нет")
    except TypeError:
        await message.answer("Nice try!")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
