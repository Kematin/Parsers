import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import AsyncGenerator, List

import aiohttp
from fake_useragent import UserAgent

UA = UserAgent()
URL = "https://cs.money/1.0/market/sell-orders"
COOKIES = {
    "group_id": "169ccdd2-99c3-484c-9e66-a3904bc0a26f",
    "onboarding__skin_quick_view": "false",
    "cf_clearance": ".mjVIH.1w3EX5Aw6hvmwCwuJK886i1RylTeDcDJx508-1709053597-1.0-AfF1w9c3Jg0x90CJl3cWdrN6j3zlCBzUo7TZSeOHWsUYOWER3L7R5I7APiQV35Ns8dBGDZuG9E/BtaYkhp13UCk=",
    "new_language": "en",
}
HEADERS = {
    "authority": "cs.money",
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "referer": "https://cs.money/market/buy/",
    "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "traceparent": "00-88d699760dfbeb9c26d94bb55706586b-a1d3883284a34495-01",
    "user-agent": UA.random,
    "x-client-app": "web",
}


@dataclass
class Item:
    name: str
    steam_price: int
    default_price: int
    price_with_discount: int
    discount: int
    float: int
    pattern: int
    csmoney_link: str


async def normalize_discount(discount: int) -> int:
    if discount > 1:
        discount /= 100
    return discount


async def make_request(url, **kwargs) -> dict | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, **kwargs) as response:
            if response.status != 200:
                return None
            return await response.json()


async def get_item(json_data: dict, discount: int):
    json_data = json_data["items"]
    for json_item in json_data:
        name = json_item["asset"]["names"]["full"]
        discount_item = json_item["pricing"]["discount"]
        if discount_item < discount:
            continue
        item = Item(
            name=name,
            steam_price=json_item["pricing"]["default"],
            default_price=json_item["pricing"]["priceBeforeDiscount"],
            price_with_discount=json_item["pricing"]["computed"],
            discount=round(discount_item, 3),
            float=json_item["asset"]["float"],
            pattern=json_item["asset"]["pattern"],
            csmoney_link=f"https://cs.money/market/buy/?search={name}".replace(
                " ", "%20"
            ),
        )
        yield item


# ! Price in dollars
async def collect_data(
    discount: int = 0,
    limit: int = 60,
    max_price: int = 10**6,
    min_price: int = 0,
    types: List[int] = [],
) -> AsyncGenerator[Item, None]:
    params = {
        "limit": limit,
        "maxPrice": max_price,
        "minPrice": min_price,
        "type": types,
    }

    num = 0
    while 1:
        params["offset"] = num * limit
        HEADERS["user-agent"] = UA.random
        json_data = await make_request(
            url=URL, headers=HEADERS, params=params, cookies=COOKIES
        )
        if json_data is None:
            logging.warning("[WARNING] Response with error | break")
            break

        async for item in get_item(json_data, discount):
            yield item

        num += 1
        logging.info(f"[INFO] Request {num} was maked")


async def bot_service(
    discount: int = 0,
    limit: int = 60,
    max_price: int = 10**6,
    min_price: int = 0,
    types: List[int] = [],
) -> AsyncGenerator[Item, None]:
    discount = await normalize_discount(discount)
    async for item in collect_data(
        discount=discount,
        limit=limit,
        max_price=max_price,
        min_price=min_price,
        types=types,
    ):
        yield item


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    async def main(
        discount: int = 0,
        limit: int = 60,
        max_price: int = 10**6,
        min_price: int = 0,
        types: List[int] = [],
    ):
        discount = await normalize_discount(discount)
        async for item in collect_data(
            discount=discount,
            limit=limit,
            max_price=max_price,
            min_price=min_price,
            types=types,
        ):
            logging.info(f"[INFO] new item {item.name}")

    params = {"discount": 30, "limit": 60, "max_price": 100, "min_price": 0}
    asyncio.run(main(**params))
