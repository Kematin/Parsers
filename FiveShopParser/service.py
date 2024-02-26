import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

import aiofiles
import aiohttp
from aiocsv import AsyncWriter
from fake_useragent import UserAgent

URL = "https://5ka.ru/api/v2/special_offers"
filename = str


@dataclass
class Promo:
    id: int
    date_begin: str
    date_end: str
    type: str
    description: str
    kind: str
    expired_at: int


@dataclass
class Prices:
    price_reg__min: int
    price_promo__min: int


@dataclass
class Product:
    id: int
    name: str
    mech: bool | None
    img_link: str
    plu: int
    promo: Promo
    current_prices: Prices
    store_name: str


async def make_request(headers={}, params={}, cookies={}, **kwargs) -> List[Product]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=URL, headers=headers, params=params, cookies=cookies, **kwargs
        ) as response:
            collected_data = list()
            data = await response.json()
            for product_json in data["results"]:
                promo = Promo(**product_json["promo"])
                prices = Prices(**product_json["current_prices"])
                product_json["promo"] = promo
                product_json["current_prices"] = prices
                product = Product(**product_json)
                collected_data.append(product)
            return collected_data


async def collect_data(store_id: str = "12122") -> List[Product]:
    ua = UserAgent()

    headers = {
        "User-Agent": ua.random,
        "Accept": "*/*",
    }
    params = {"records_per_page": 20, "page": 1, "store": store_id}

    collect_data = list()
    page = 1
    while True:
        try:
            products = await make_request(headers=headers, params=params)
            if len(products) == 0:
                break
            collect_data += products
            page += 1
            params["page"] = page
            headers["User-Agent"] = ua.random
            logging.info(f"Add page {page-1}")
        except KeyError:
            logging.info(f"KEY ERROR AT PAGE {page+1}")
            break
    return collect_data


async def get_converted_data(date_begin: str, date_end: str) -> str:
    date_begin_obj = datetime.strptime(date_begin, "%Y-%m-%d")
    date_end_obj = datetime.strptime(date_end, "%Y-%m-%d")

    formatted_date_begin = date_begin_obj.strftime("%d %B")
    formatted_date_end = date_end_obj.strftime("%d %B")

    date_range = f"{formatted_date_begin} to {formatted_date_end}"
    return date_range


async def get_procent(previous_price: int, new_price: int):
    difference = previous_price - new_price
    return round(difference / (previous_price / 100), 2)


async def normalize_filename(name: str = "City"):
    cur_time = datetime.now().strftime("%d_%m_%Y_%H_%M")
    city_name = name.split(" ")[0][2:]
    filename = f"{city_name}_{cur_time}.csv"
    return filename


async def write_to_csv(
    data: List[Product],
    name: str = "City",
) -> filename:
    filename = await normalize_filename(name)
    async with aiofiles.open(filename, "w") as file:
        writer = AsyncWriter(file)
        await writer.writerow(
            (
                "Продукт",
                "Старая цена",
                "Новая цена",
                "Процент скидки",
                "Время проведения акции",
                "Изображение",
            )
        )
        for product in data:
            date = await get_converted_data(
                product.promo.date_begin, product.promo.date_end
            )
            procent = await get_procent(
                product.current_prices.price_reg__min,
                product.current_prices.price_promo__min,
            )
            await writer.writerow(
                (
                    product.name,
                    product.current_prices.price_reg__min,
                    product.current_prices.price_promo__min,
                    procent,
                    date,
                    product.img_link,
                )
            )
    logging.info(f"Файл: {filename} записан.")
    return filename


async def main_service(store_id: str = "31Z6") -> filename:
    data = await collect_data(store_id=store_id)
    filename = await write_to_csv(data, name=data[0].store_name)
    return filename


if __name__ == "__main__":
    asyncio.run(main_service())
