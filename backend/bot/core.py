import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update, Message
from fastapi import APIRouter, Request, HTTPException

import selarti
from service import fetch_user_by_id, create_user
from utils import validate_env

logger = logging.getLogger(__name__)

router = APIRouter()
tg_router = Router()

bot: Bot
dp: Dispatcher


@tg_router.message(F.text.startswith("/start"))
async def start(message: Message):
    try:
        db_user = await fetch_user_by_id(message.from_user.id, True)
    except HTTPException as e:
        if e.status_code == 404:
            ref_id = None
            parts = message.text.replace("/start", "").strip().replace("_", " ").split()
            if len(parts) >= 1 and parts[0].isdigit():
                ref_tg_id = int(parts[0])
                try:
                    ref_user = await fetch_user_by_id(ref_tg_id, True)
                    ref_id = ref_user['id']
                except Exception as ex:
                    logger.error(f"Failed to find referrer {ref_tg_id}: {ex}")
            db_user = await create_user(message.from_user.model_dump(), ref_id)
            if message.from_user.username:
                await selarti.add_target(message.from_user.username)
        else:
            raise
    if db_user:
        await message.answer(f"Добро пожаловать в Cardinal, {db_user['username']}")
    else:
        await message.answer("Добро пожаловать в Cardinal.\nВ данный момент мы ведём работы над сервисом, попробуйте позже")


@router.post("/webhook")
async def webhook(request: Request):
    update_data = await request.json()
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)


async def init_webhook():
    global bot, dp
    validate_env("BOT_TOKEN")
    validate_env("WEBHOOK_KEY")
    validate_env("WEBHOOK_URL")

    bot = Bot(token=os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(tg_router)

    webhook_url = os.environ["WEBHOOK_URL"]
    if webhook_url.endswith("/"):
        webhook_url = webhook_url[:-1]
    await bot.set_webhook(f"{webhook_url}/api/webhook", secret_token=os.environ["WEBHOOK_KEY"])
    logger.info(f"Telegram webhook set to {webhook_url}/api/webhook")
