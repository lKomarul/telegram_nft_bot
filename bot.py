import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import aiohttp

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 5))
MAX_PRICE = float(os.getenv("MAX_PRICE", 1000))
RARITY_FILTER = os.getenv("RARITY_FILTER", "").split(",")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

NFT_API_URL = "https://example.com/api/limited_nft"

already_seen = {}

async def check_nft():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(NFT_API_URL) as resp:
                    data = await resp.json()
                    gifts = data.get("gifts", [])
                    for item in gifts:
                        gift_id = item["id"]
                        price = float(item.get("price", 0))
                        rarity = item.get("rarity", "").lower()
                        supply = int(item.get("supply", 1))
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        if price <= MAX_PRICE and (not RARITY_FILTER or rarity in RARITY_FILTER):
                            if gift_id not in already_seen:
                                already_seen[gift_id] = {'name': item['name'], 'sold': False}
                                msg = (
                                    f"🎁 <b>Новый лимитированный NFT!</b>\n"
                                    f"Название: {item['name']}\n"
                                    f"Цена: {price}\n"
                                    f"Редкость: {rarity}\n"
                                    f"Остаток: {supply}\n"
                                    f"<a href='{item['link']}'>Ссылка</a>\n"
                                    f"<i>Время обнаружения: {timestamp}</i>"
                                )
                                image_url = item.get("image")
                                if image_url:
                                    await bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=msg, parse_mode=ParseMode.HTML)
                                else:
                                    await bot.send_message(chat_id=CHAT_ID, text=msg)
                                print(f"[{timestamp}] Новый NFT: {item['name']} Остаток: {supply}")
                            else:
                                if not already_seen[gift_id]['sold'] and supply == 0:
                                    already_seen[gift_id]['sold'] = True
                                    msg = (
                                        f"❌ <b>Подарок раскуплен!</b>\n"
                                        f"Название: {item['name']}\n"
                                        f"<i>Время распродажи: {timestamp}</i>"
                                    )
                                    await bot.send_message(chat_id=CHAT_ID, text=msg)
                                    print(f"[{timestamp}] Подарок раскуплен: {item['name']}")
            except Exception as e:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Ошибка при проверке NFT:", e)

            await asyncio.sleep(CHECK_INTERVAL)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("Бот запущен. Мониторинг лимитированных NFT активен!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_nft())
    executor.start_polling(dp, skip_updates=True)
