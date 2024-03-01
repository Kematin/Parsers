import asyncio
import logging
import sys
from os import environ

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

import service

load_dotenv()

token = environ.get("TOKEN")
dp = Dispatcher()
bot = Bot(token, parse_mode=ParseMode.HTML)
settings = {}


class ChangeSettings(StatesGroup):
    choose_min_price = State()
    choose_max_price = State()
    choose_discount = State()
    max_items_count = State()


async def make_skin_message(message: Message, item: service.Item):
    discount = item.discount * 100
    await message.answer(
        f"<b>{item.name}</b>\n\n"
        + f"Цена: {item.price_with_discount}$\n"
        + f"Цена в стиме: {item.steam_price}$\n"
        + f"Скидка: {discount}%\n"
        + f"Float: {item.float}\n"
        + f"Pattern: {item.pattern}\n"
        + f"Ссылка: {item.csmoney_link}"
    )


async def get_skins_handler(message: Message):
    settings_data = settings[message.from_user.id]
    min_price = settings_data["choose_min_price"]
    max_price = settings_data["choose_max_price"]
    discount = settings_data["choose_discount"]
    max_items = settings_data["max_items_count"]
    count = 0
    async for item in service.bot_service(
        discount=discount, max_price=max_price, min_price=min_price
    ):
        await make_skin_message(message, item)
        count += 1
        if count == max_items:
            return
    await message.answer(text="Больше предметов не найдено")


async def change_settings_handler(message: Message, state: FSMContext):
    await message.answer(text="Напишите минимальную цену <b>($)</b>:")
    await state.set_state(ChangeSettings.choose_min_price)


@dp.message(ChangeSettings.choose_min_price)
async def choose_min_price(message: Message, state: FSMContext):
    message_text = message.text.lower()
    if not message_text.isdigit():
        await state.set_state(None)
        await change_settings_handler(message, state)
        return
    await state.update_data(choose_min_price=int(message_text))
    await message.answer(text="Напишите максимальную цену <b>($)</b>:")
    await state.set_state(ChangeSettings.choose_max_price)


@dp.message(ChangeSettings.choose_max_price)
async def choose_max_price(message: Message, state: FSMContext):
    message_text = message.text.lower()
    if not message_text.isdigit():
        await message.answer(text="Напишите максимальную цену <b>($)</b>:")
        return
    await state.update_data(choose_max_price=int(message_text))
    await message.answer(text="Напишите желаемую скидку <b>(%)</b>:")
    await state.set_state(ChangeSettings.choose_discount)


@dp.message(ChangeSettings.choose_discount)
async def choose_discount(message: Message, state: FSMContext):
    message_text = message.text.lower()
    if not message_text.isdigit():
        await message.answer(text="Напишите желаемую скидку <b>(%)</b>:")
        return
    await state.update_data(choose_discount=int(message_text))
    await message.answer(text="Напишите максимальное количество предметов:")
    await state.set_state(ChangeSettings.max_items_count)


@dp.message(ChangeSettings.max_items_count)
async def choose_max_items(message: Message, state: FSMContext):
    message_text = message.text.lower()
    if not message_text.isdigit():
        await message.answer(text="Напишите максимальное количество предметов:")
        return
    await state.update_data(max_items_count=int(message_text))
    settings[message.from_user.id] = await state.get_data()
    await state.clear()
    await get_settings(message)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    settings[message.from_user.id] = None
    get_skin_button = KeyboardButton(text="Получить скины")
    change_settings_button = KeyboardButton(text="Изменить настройки")
    get_settings_button = KeyboardButton(text="Посмотреть настройки")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[get_skin_button], [change_settings_button, get_settings_button]],
        resize_keyboard=True,
    )
    await message.answer("CSMoney Бот", reply_markup=keyboard)


@dp.message(StateFilter(None), F.text.lower() == "получить скины")
async def get_skins(message: types.Message, state: FSMContext) -> None:
    if settings.get(message.from_user.id, None) is None:
        await message.answer(text="Перед получением предметов пропишите настройки")
        await change_settings_handler(message, state)
    else:
        await get_skins_handler(message)


@dp.message(StateFilter(None), F.text.lower() == "изменить настройки")
async def change_settings(message: types.Message, state: FSMContext) -> None:
    await change_settings_handler(message, state)


@dp.message(F.text.lower() == "посмотреть настройки")
async def get_settings(message: types.Message) -> None:
    if settings.get(message.from_user.id, None) is None:
        await message.answer("Текущих настроек нет")
    else:
        settings_data = settings[message.from_user.id]
        await message.answer(
            "Ваши текущие настройки\n\n" "Мин цена - {}$\n".format(
                settings_data["choose_min_price"]
            )
            + "Макс цена - {}$\n".format(settings_data["choose_max_price"])
            + "Желаемая скидка - {}%\n".format(settings_data["choose_discount"])
            + "Максимальное количество предметов - {}".format(
                settings_data["max_items_count"]
            )
        )


@dp.message()
async def error_handler(message: types.Message) -> None:
    await message.reply("Такой команды нет")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
