import asyncio
import logging
import sys
from os import environ

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

import service

load_dotenv()

token = environ.get("TOKEN")
dp = Dispatcher()
bot = Bot(token, parse_mode=ParseMode.HTML)
settings = {}


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    message.answer("Отправь название города")


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
