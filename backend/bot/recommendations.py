import asyncio
import logging
import os
from datetime import datetime, timezone
from textwrap import dedent

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from fastapi import APIRouter, HTTPException, Request

from bot.buttons import CARDINAL_SUPPORT, NO_CORE_CHANNEL_BUTTONS, NOT_CARDINAL_USER_BUTTONS, SUBSCRIPTION_SELECT_BUTTONS_NO_BACK
from bot.notification.notification import NotificationType
from bot.notification.queue import push_notification_with_payload
from bot.texts import (
    DECLINE_RECOMMENDATION_EXTRACT_RULES_FAILED,
    DECLINE_RECOMMENDATION_NEED_INFO,
    DECLINE_RECOMMENDATION_QUESTION,
    DECLINE_RECOMMENDATION_RULE_ADDED,
    NO_CORE_CHANNEL,
    NOT_CARDINAL_USER,
    RECOMMENDATION_ACCEPTED,
    RECOMMENDATION_ERROR,
    RECOMMENDATIONS_LINK_CHANNEL_FAILED,
    RECOMMENDATIONS_START,
    RECOMMENDATIONS_START_2,
    SUBSCRIPTION_SELECT,
    UNSUBSCRIBED_DAILY,
    UNSUBSCRIBED_FOUND,
)
from consts import UserChannelType
from external.ai import check_rules, extract_rules
from external.embedding import accept_recommendation, decline_recommendation
from service.channels import fetch_user_channels_by_user_id, verify_user_channel
from service.db import get_pool
from service.finder import fetch_task_title_by_id, increment_stats
from service.metrics import leads_actions_total, leads_time, users_linked_total
from service.recommendations import delete_user_recommendation, fetch_recommendation_by_id
from service.task_rules import fetch_user_rules, save_user_rules
from service.users import fetch_user_by_id
from utils import escape_markdown_v2, is_subscription_expired, validate_env

logger = logging.getLogger(__name__)

router = APIRouter()
tg_router = Router()

bot: Bot
dp: Dispatcher


class DeclineFlow(StatesGroup):
    waiting_for_user_description = State()


async def send_no_core_channel(chat_id, _):
    try:
        await bot.send_message(chat_id=chat_id, text=NO_CORE_CHANNEL, reply_markup=NO_CORE_CHANNEL_BUTTONS)
    except Exception as e:
        logger.warning(f"Failed to send no_core_channel message to {chat_id}: {e}")


async def send_unsubscribed_found(chat_id, payload):
    text = UNSUBSCRIBED_FOUND.format(task_title=payload["task_title"])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💳 Активировать тариф", callback_data="subscription_select")]])
    await bot.send_message(chat_id=chat_id, text=dedent(text), reply_markup=keyboard)


async def send_unsubscribed_daily(chat_id, payload):
    text = UNSUBSCRIBED_DAILY.format(found_total=payload["found_total"])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💳 Продлить доступ", callback_data="subscription_select")]])
    await bot.send_message(chat_id=chat_id, text=dedent(text), reply_markup=keyboard)


async def send_recommendation_to_user(recommendation):
    async with get_pool().acquire() as conn:
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1;", recommendation.user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail=f"Subscription for {recommendation.user_id} not found")

    if is_subscription_expired(subscription):
        user_id = subscription["user_id"]
        task_title = await fetch_task_title_by_id(user_id, recommendation.task_id)
        payload = {"subscription": subscription, "task_title": task_title, "date": recommendation.message_created_at}
        await push_notification_with_payload(user_id, NotificationType.UNSUBSCRIBED_FOUND, payload)
        raise HTTPException(status_code=402, detail=f"Subscription {subscription['id']} is expired")

    rules = await fetch_user_rules(recommendation.user_id, recommendation.task_id)
    if rules and not await check_rules(recommendation.text, rules):
        logger.debug(f"User recommendation {recommendation.id} skipped due to rules")
        await delete_user_recommendation(recommendation.user_id, recommendation.id)
        logger.debug(f"User recommendation {recommendation.id} removed due to rules")
        return

    user_chats = await fetch_user_channels_by_user_id(recommendation.user_id, UserChannelType.RECOMMENDATION)
    if not user_chats:
        raise HTTPException(status_code=404, detail="User didn't attach any chat to itself")

    task_title = await fetch_task_title_by_id(recommendation.user_id, recommendation.task_id)
    keyboard = _recommendation_keyboard(recommendation.id)

    if recommendation.message_created_at.tzinfo is None:
        message_created_at = recommendation.message_created_at.replace(tzinfo=timezone.utc)
    else:
        message_created_at = recommendation.message_created_at

    now = datetime.now(timezone.utc)
    leads_time.observe((now - message_created_at).total_seconds())

    for chat in user_chats:
        try:
            if recommendation.username:
                title = f"Новое предложение от @{recommendation.username} по задаче {task_title}"
            else:
                title = f"Новое предложение по задаче {task_title}"
            title = escape_markdown_v2(title)
            text = escape_markdown_v2(recommendation.text)
            await bot.send_message(chat_id=chat["chat_id"], text=f"{title}:\n> {text}", reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Failed to send to {chat['chat_id']} for {chat['user_id']}: {e}")

    await increment_stats(recommendation.task_id)


@tg_router.message(F.text.startswith("/start"))
async def start(message: Message):
    try:
        user = await fetch_user_by_id(message.from_user.id, True)
    except Exception as e:
        logger.warning(f"Failed to link recommendations channel id: {e}")
        await bot.send_message(chat_id=message.chat.id, text=dedent(NOT_CARDINAL_USER), reply_markup=NOT_CARDINAL_USER_BUTTONS)
        return
    try:
        linked = await verify_user_channel(user["id"], message.chat.id, UserChannelType.RECOMMENDATION)
        if linked:
            users_linked_total.inc()
        await bot.send_message(chat_id=message.chat.id, text=RECOMMENDATIONS_START, parse_mode=ParseMode.MARKDOWN_V2)
        await bot.send_message(chat_id=message.chat.id, text=RECOMMENDATIONS_START_2, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.warning(f"Failed to link recommendations channel id: {e}")
        await bot.send_message(chat_id=message.chat.id, text=RECOMMENDATIONS_LINK_CHANNEL_FAILED)


@tg_router.callback_query(F.data == "subscription_select")
async def _subscription_select(callback: CallbackQuery):
    try:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dedent(SUBSCRIPTION_SELECT), reply_markup=SUBSCRIPTION_SELECT_BUTTONS_NO_BACK)
    except Exception as e:
        logger.warning(f'Failed to process callback "subscription_select" from {callback.from_user.id}: {e}')


@tg_router.callback_query(F.data.startswith("ra_"))
async def accept_callback(callback: CallbackQuery):
    rec_id = callback.data.split("_", 1)[1]
    try:
        await accept_recommendation(rec_id)
        await _finish_recommendation(callback)
        leads_actions_total.labels(action="accept").inc()
        await bot.send_message(chat_id=callback.message.chat.id, text=dedent(RECOMMENDATION_ACCEPTED), reply_to_message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to accept recommendation: {e}")
        await _send_fail(callback.message.chat.id, callback.message.message_id, RECOMMENDATION_ERROR)


@tg_router.callback_query(F.data.startswith("rd_"))
async def decline_callback(callback: CallbackQuery, state: FSMContext):
    rec_id = callback.data.split("_", 1)[1]
    try:
        question = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=dedent(DECLINE_RECOMMENDATION_QUESTION),
            reply_to_message_id=callback.message.message_id,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data=f"rdc_{rec_id}")]]),
        )
        await state.update_data(text=callback.message.text, message_id=callback.message.message_id, question_id=question.message_id, rec_id=rec_id)
        await state.set_state(DeclineFlow.waiting_for_user_description)
        await _finish_recommendation(callback)
    except Exception as e:
        logger.warning(f"Failed to decline recommendation: {e}")
        await _send_fail(callback.message.chat.id, callback.message.message_id, RECOMMENDATION_ERROR)


@tg_router.callback_query(F.data.startswith("rdc_"))
async def decline_cancel(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        rec_id = data.get("rec_id")
        additional_messages = data.get("additional_messages")
        if not additional_messages:
            additional_messages = []

        if rec_id and await state.get_state() == DeclineFlow.waiting_for_user_description:
            message_id = data["message_id"]
            await state.clear()

            await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=message_id, reply_markup=_recommendation_keyboard(rec_id))

            await bot.delete_message(callback.message.chat.id, callback.message.message_id)
            for additional_message in additional_messages:
                await bot.delete_message(callback.message.chat.id, additional_message)
        else:
            logger.warning(f"Cancel recommendation decline with wrong state for {rec_id} in {callback.message.chat.id}")
            await _send_fail(callback.message.chat.id, callback.message.message_id, RECOMMENDATION_ERROR)
    except Exception as e:
        logger.warning(f"Failed to cancel recommendation decline: {e}")
        await _send_fail(callback.message.chat.id, callback.message.message_id, RECOMMENDATION_ERROR)


@tg_router.message(DeclineFlow.waiting_for_user_description, F.text)
async def handle_decline(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data["text"]
    rec_id = data["rec_id"]
    question_id = data["question_id"]
    additional_messages = data.get("additional_messages")
    if not additional_messages:
        additional_messages = []

    feedback = data.get("feedback")
    if not feedback:
        feedback = message.text
    else:
        feedback = feedback + ";\n" + message.text

    rules = await extract_rules(text, feedback)

    try:
        if len(rules) == 1 and rules[0] == "insufficient data":
            question = await bot.send_message(chat_id=message.chat.id, text=DECLINE_RECOMMENDATION_NEED_INFO, reply_to_message_id=message.message_id)
            additional_messages.append(question.message_id)
            await state.update_data(feedback=feedback, additional_messages=additional_messages)
        else:
            recommendation = await fetch_recommendation_by_id(rec_id)
            await save_user_rules(recommendation["user_id"], recommendation["task_id"], rules)
            await message.answer(dedent(DECLINE_RECOMMENDATION_RULE_ADDED))
            await state.clear()
            await decline_recommendation(rec_id)
            leads_actions_total.labels(action="decline").inc()
    except Exception as e:
        logger.warning(f"Failed to extract rules for recommendations: {e}")
        await _send_fail(message.chat.id, question_id, DECLINE_RECOMMENDATION_EXTRACT_RULES_FAILED, additional_messages)


def _recommendation_keyboard(rec_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подходит", callback_data=f"ra_{rec_id}"), InlineKeyboardButton(text="Не подходит", callback_data=f"rd_{rec_id}")],
            [InlineKeyboardButton(text="Не нашёл автора", url=CARDINAL_SUPPORT)],
        ]
    )


async def _finish_recommendation(callback: CallbackQuery):
    try:
        new_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=new_keyboard)
    except Exception as e:
        logger.warning(f"Failed to finish recommendation in {callback.message.chat.id}: {e}")


async def _send_fail(chat_id, message_id, text, additional_messages=None):
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
    if additional_messages:
        for additional_message in additional_messages:
            await bot.delete_message(chat_id, additional_message)
    await asyncio.sleep(5)
    await bot.delete_message(chat_id, message_id)


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

    bot = Bot(token=os.environ["RECOMMENDATION_BOT_TOKEN"], default=DefaultBotProperties(parse_mode="HTML"))
    redis_host = os.environ.get("REDIS_HOST", "redis")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    storage = RedisStorage.from_url(f"redis://:{os.environ["REDIS_PASSWORD"]}@{redis_host}:{redis_port}/0")
    dp = Dispatcher(storage=storage)
    dp.include_router(tg_router)

    webhook_url = os.environ["WEBHOOK_URL"]
    if webhook_url.endswith("/"):
        webhook_url = webhook_url[:-1]
    await bot.set_webhook(f"{webhook_url}/api/finder/recommendations/webhook", secret_token=os.environ["WEBHOOK_KEY"])
    logger.info(f"Telegram recommendations webhook set to {webhook_url}/api/finder/recommendations/webhook")
