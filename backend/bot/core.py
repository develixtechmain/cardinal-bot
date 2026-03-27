import logging
import os
from textwrap import dedent

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, Message, Update
from fastapi import APIRouter, HTTPException, Request

from bot.buttons import (
    ABOUT_VIDEO_BUTTONS,
    ABOUT_VIDEO_BUTTONS_FIRST,
    CARDINAL_CORE_BUTTONS,
    CARDINAL_VIDEO,
    FIRST_BRIEFING_COMPLETED_BUTTONS,
    PURCHASE_DONE_BUTTONS,
    PURCHASE_DONE_BUTTONS_FIRST,
    PURCHASE_FAILED_BUTTONS,
    QUICKSTART_BUTTONS,
    QUICKSTART_BUTTONS_FIRST,
    QUICKSTART_VIDEO_BUTTONS,
    QUICKSTART_VIDEO_BUTTONS_FIRST,
    SUBSCRIPTION_BUTTONS,
    SUBSCRIPTION_BUTTONS_FIRST,
    SUBSCRIPTION_EXPIRED_BUTTONS,
    SUBSCRIPTION_SELECT_BUTTONS,
    SUBSCRIPTION_TRIAL_BUTTONS,
)
from bot.texts import (
    BUTTONS_QUICKSTART,
    CARDINAL_ACTIVATED,
    CARDINAL_ERROR,
    CARDINAL_RETURN,
    CARDINAL_START,
    CARDINAL_START_2,
    CARDINAL_VIDEO_TEXT,
    FIRST_BRIEFING_COMPLETED,
    LINK_CORE_CHANNEL_FAILED,
    PURCHASE_FAILED,
    SUBSCRIPTION,
    SUBSCRIPTION_EXPIRED,
    SUBSCRIPTION_PROLONGED,
    SUBSCRIPTION_SELECT,
    SUBSCRIPTION_TRIAL,
    TRIAL_ACTIVATED,
    TRIAL_ENDED,
    TRIAL_USED,
)
from consts import UserChannelType
from service.channels import verify_user_channel
from service.subscriptions import fetch_subscription_by_user_id, start_subscription_trial
from service.users import create_user, fetch_user_by_id
from utils import validate_env

logger = logging.getLogger(__name__)

router = APIRouter()
tg_router = Router()

bot: Bot
dp: Dispatcher


async def send_purchase_done(chat_id, payload):
    if payload["first"]:
        text = CARDINAL_ACTIVATED
        keyboard = PURCHASE_DONE_BUTTONS_FIRST
    else:
        text = SUBSCRIPTION_PROLONGED
        keyboard = PURCHASE_DONE_BUTTONS

    await bot.send_message(chat_id=chat_id, text=dedent(text), reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2)


async def send_trial_ended(chat_id, _):
    await bot.send_message(chat_id=chat_id, text=dedent(TRIAL_ENDED), reply_markup=SUBSCRIPTION_EXPIRED_BUTTONS)


async def send_unsubscribed(chat_id, _):
    await bot.send_message(chat_id=chat_id, text=dedent(SUBSCRIPTION_EXPIRED), reply_markup=SUBSCRIPTION_EXPIRED_BUTTONS)


async def send_purchase_failed(chat_id, _):
    await bot.send_message(chat_id=chat_id, text=dedent(PURCHASE_FAILED), reply_markup=PURCHASE_FAILED_BUTTONS)


async def send_briefing_completed(chat_id, _):
    await bot.send_message(chat_id=chat_id, text=dedent(FIRST_BRIEFING_COMPLETED), reply_markup=FIRST_BRIEFING_COMPLETED_BUTTONS)


@tg_router.message(F.text.startswith("/start"))
async def start(message: Message):
    logger.info(f"Message: {message}")
    first_time = False
    try:
        db_user = await fetch_user_by_id(message.from_user.id, True)
    except HTTPException as e:
        if e.status_code == 404:
            first_time = True
            ref_id = None
            parts = message.text.replace("/start", "").strip().replace("_", " ").split()
            if len(parts) >= 1 and parts[1].isdigit():
                ref_tg_id = int(parts[1])
                try:
                    ref_user = await fetch_user_by_id(ref_tg_id, True)
                    ref_id = ref_user["id"]
                except Exception as ex:
                    logger.error(f"Failed to find referrer {ref_tg_id}: {ex}")
            db_user = await create_user(message.from_user.model_dump(), ref_id)
        else:
            raise
    if db_user:
        try:
            await verify_user_channel(db_user["id"], message.chat.id, UserChannelType.CORE)
            if first_time:
                await message.answer(dedent(CARDINAL_START))
                await message.answer(dedent(CARDINAL_START_2 if first_time else CARDINAL_RETURN), reply_markup=CARDINAL_CORE_BUTTONS, parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await message.answer(dedent(CARDINAL_RETURN), reply_markup=CARDINAL_CORE_BUTTONS)
        except Exception as e:
            logger.warning(f"Failed to link core channel id: {e}")
            await bot.send_message(chat_id=message.chat.id, text=LINK_CORE_CHANNEL_FAILED)
    else:
        await message.answer(CARDINAL_ERROR)


@tg_router.callback_query(F.data == "quickstart")
async def _quickstart(callback: CallbackQuery):
    try:
        keyboard = QUICKSTART_BUTTONS_FIRST if await _is_first(callback.from_user.id) else QUICKSTART_BUTTONS
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(BUTTONS_QUICKSTART), reply_markup=keyboard)
    except Exception as e:
        logger.warning(f'Failed to process callback "quickstart" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "quickstart_video")
async def _quickstart_video(callback: CallbackQuery):
    try:
        keyboard = QUICKSTART_VIDEO_BUTTONS_FIRST if await _is_first(callback.from_user.id) else QUICKSTART_VIDEO_BUTTONS
        await bot.send_video(chat_id=callback.message.chat.id, caption=CARDINAL_VIDEO_TEXT, video=CARDINAL_VIDEO, supports_streaming=True, protect_content=True, reply_markup=keyboard)
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f'Failed to process callback "quickstart_video" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "quickstart_video_trial")
async def _quickstart_video_trial(callback: CallbackQuery):
    try:
        await _start_trial(callback.from_user.id)
        await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=QUICKSTART_VIDEO_BUTTONS)
    except Exception as e:
        logger.warning(f'Failed to process callback "quickstart_video_trial" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "quickstart_video_back")
async def _quickstart_video_back(callback: CallbackQuery):
    try:
        keyboard = QUICKSTART_BUTTONS_FIRST if await _is_first(callback.from_user.id) else QUICKSTART_BUTTONS
        await bot.send_message(chat_id=callback.message.chat.id, text=dedent(BUTTONS_QUICKSTART), reply_markup=keyboard)
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f'Failed to process callback "quickstart_video_back" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "quickstart_trial")
async def _quickstart_trial(callback: CallbackQuery):
    try:
        await _start_trial(callback.from_user.id)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(TRIAL_ACTIVATED), reply_markup=QUICKSTART_BUTTONS)
    except Exception as e:
        logger.warning(f'Failed to process callback "quickstart_trial" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "quickstart_back")
async def _quickstart_back(callback: CallbackQuery):
    try:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(CARDINAL_RETURN), reply_markup=CARDINAL_CORE_BUTTONS)
    except Exception as e:
        logger.warning(f'Failed to process callback "quickstart_back" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "subscription")
async def _subscription(callback: CallbackQuery):
    try:
        first = await _is_first(callback.from_user.id)
        if first:
            text = SUBSCRIPTION_TRIAL
            keyboard = SUBSCRIPTION_BUTTONS_FIRST
        else:
            text = SUBSCRIPTION
            keyboard = SUBSCRIPTION_BUTTONS
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(text), reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.warning(f'Failed to process callback "subscription" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "subscription_trial")
async def _subscription_trial(callback: CallbackQuery):
    try:
        text = TRIAL_ACTIVATED if await _start_trial(callback.from_user.id) else TRIAL_USED
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(text), reply_markup=SUBSCRIPTION_TRIAL_BUTTONS)
    except Exception as e:
        logger.warning(f'Failed to process callback "subscription_trial" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "subscription_select")
async def _subscription_select(callback: CallbackQuery):
    try:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(SUBSCRIPTION_SELECT), reply_markup=SUBSCRIPTION_SELECT_BUTTONS)
    except Exception as e:
        logger.warning(f'Failed to process callback "subscription_select" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "subscription_back")
async def _subscription_back(callback: CallbackQuery):
    try:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(CARDINAL_RETURN), reply_markup=CARDINAL_CORE_BUTTONS)
    except Exception as e:
        logger.warning(f'Failed to process callback "subscription_back" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "about_video")
async def _about_video(callback: CallbackQuery):
    try:
        keyboard = ABOUT_VIDEO_BUTTONS_FIRST if await _is_first(callback.from_user.id) else ABOUT_VIDEO_BUTTONS
        await bot.send_video(chat_id=callback.message.chat.id, caption=CARDINAL_VIDEO_TEXT, video=CARDINAL_VIDEO, supports_streaming=True, protect_content=True, reply_markup=keyboard)
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except Exception as e:
        logger.warning(f'Failed to process callback "about_video" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "about_video_trial")
async def _about_video_trial(callback: CallbackQuery):
    try:
        await _start_trial(callback.from_user.id)
        await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=ABOUT_VIDEO_BUTTONS)
    except Exception as e:
        logger.warning(f'Failed to process callback "about_video_trial" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data == "about_video_back")
async def _about_video_back(callback: CallbackQuery):
    try:
        await bot.send_message(chat_id=callback.message.chat.id, text=dedent(CARDINAL_RETURN), reply_markup=CARDINAL_CORE_BUTTONS)
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f'Failed to process callback "about_video_back" from {callback.from_user.id}: {e}')


async def _is_first(tg_user_id):
    subscription = await fetch_subscription_by_user_id(tg_user_id, True)
    return not subscription["trial_starts_at"] and not subscription["trial_ends_at"] and not subscription["subscription_ends_at"]


async def _start_trial(tg_user_id):
    subscription = await fetch_subscription_by_user_id(tg_user_id, True)
    if not subscription["trial_starts_at"] and not subscription["trial_ends_at"] and not subscription["subscription_ends_at"]:
        await start_subscription_trial(subscription["user_id"], subscription["id"])
        return True
    else:
        return False


@router.post("/webhook")
async def webhook(request: Request):
    update_data = await request.json()
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)


async def init_webhook():
    global bot, dp
    validate_env("BOT_TOKEN")
    validate_env("REDIS_PASSWORD")
    validate_env("WEBHOOK_KEY")
    validate_env("WEBHOOK_URL")

    bot = Bot(token=os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode="HTML"))
    redis_host = os.environ.get("REDIS_HOST", "redis")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    storage = RedisStorage.from_url(f"redis://:{os.environ["REDIS_PASSWORD"]}@{redis_host}:{redis_port}/0")
    dp = Dispatcher(storage=storage)
    dp.include_router(tg_router)

    webhook_url = os.environ["WEBHOOK_URL"]
    if webhook_url.endswith("/"):
        webhook_url = webhook_url[:-1]
    await bot.set_webhook(f"{webhook_url}/api/webhook", secret_token=os.environ["WEBHOOK_KEY"])
    logger.info(f"Telegram webhook set to {webhook_url}/api/webhook")
