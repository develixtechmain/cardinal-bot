import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from fastapi import APIRouter, Request

import embedding
from db import fetch_user_channels_by_user_id, fetch_user_by_id, save_user_channel
from utils import validate_env

logger = logging.getLogger(__name__)

router = APIRouter()
tg_router = Router()

bot: Bot
dp: Dispatcher


async def send_recommendation_to_user(recommendation):
    user_chats = await fetch_user_channels_by_user_id(recommendation.user_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подходит", callback_data=f"ra_{recommendation.id}"),
            InlineKeyboardButton(text="Не подходит", callback_data=f"rd_{recommendation.id}"),
            InlineKeyboardButton(text="Сгенерировать", callback_data=f"rg_{recommendation.id}")
        ]
    ])

    for chat in user_chats:
        try:
            await bot.send_message(
                chat_id=chat["chat_id"],
                text=f"Предложение от {('@' + recommendation.username) or 'Unknown'}:\n{recommendation.text}",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send to {chat['chat_id']}: {e}")


@tg_router.message(F.text.startswith("/start"))
async def start(message: Message):
    try:
        user = await fetch_user_by_id(message.from_user.id, True)
    except Exception as e:
        logger.warning(f"Failed to link recommendations channel id: {e}")
        await bot.send_message(chat_id=message.chat.id, text=f"Пользователь не найден. Вы точно пользователь Cardinal?")
        return None
    try:
        linked = await save_user_channel(user["id"], message.chat.id)
        if linked:
            await message.answer(f"Добро пожаловать! В этот канал вам будут приходить ваши лиды")
        else:
            await message.answer(f"Ваши лиды ждут вас!")
    except Exception as e:
        logger.warning(f"Failed to link recommendations channel id: {e}")
        await bot.send_message(chat_id=message.chat.id, text=f"Ошибка во время привязки канала лидов к пользователю Cardinal. Попробуйте позже ещё раз")
        return None


@tg_router.callback_query(F.data.startswith("ra_"))
async def accept_callback(callback: CallbackQuery):
    rec_id = callback.data.split("_", 1)[1]
    try:
        await embedding.accept_recommendation(rec_id)
        await finish_recommendation(callback, rec_id)
    except Exception as e:
        logger.warning(f"Failed to accept recommendation: {e}")
        await bot.send_message(chat_id=callback.message.chat.id, text="Произошла ошибка с дообучением, попробуйте позже", reply_to_message_id=callback.message.message_id)
        return None


@tg_router.callback_query(F.data.startswith("rd_"))
async def decline_callback(callback: CallbackQuery):
    rec_id = callback.data.split("_", 1)[1]
    try:
        await embedding.decline_recommendation(rec_id)
        await finish_recommendation(callback, rec_id)
    except Exception as e:
        logger.warning("Failed to decline recommendation", e)
        await bot.send_message(chat_id=callback.message.chat.id, text="Произошла ошибка с дообучением, попробуйте позже", reply_to_message_id=callback.message.message_id)
        return None


@tg_router.callback_query(F.data.startswith("rg_"))
async def generate_callback(callback: CallbackQuery):
    try:
        await bot.send_message(chat_id=callback.message.chat.id, text="Сгенерирован ответ", reply_to_message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to send recommendation channel id: {e}")
        return None


async def finish_recommendation(callback: CallbackQuery, rec_id: str):
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сгенерировать", callback_data=f"rg_{rec_id}")
        ]
    ])
    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=new_keyboard)


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

    bot = Bot(token=os.environ["RECOMMENDATION_BOT_TOKEN"], default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(tg_router)

    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url.endswith("/"):
        webhook_url = webhook_url[:-1]
    await bot.set_webhook(f"{webhook_url}/api/finder/recommendations/webhook", secret_token=os.environ.get("WEBHOOK_KEY"))
    logger.info(f"Telegram recommendations webhook set to {webhook_url}/api/finder/recommendations/webhook")
