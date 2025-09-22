import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from fastapi import APIRouter, Request

import ai
import embedding
from ai import check_rules
from service import fetch_user_channels_by_user_id, fetch_user_by_id, save_user_channel
from service.recommendations import delete_user_recommendation, fetch_recommendation_by_id
from service.task_rules import fetch_user_rules, save_user_rules
from utils import validate_env

logger = logging.getLogger(__name__)

router = APIRouter()
tg_router = Router()

bot: Bot
dp: Dispatcher


class DeclineFlow(StatesGroup):
    waiting_for_user_description = State()


async def send_recommendation_to_user(recommendation):
    rules = await fetch_user_rules(recommendation.user_id, recommendation.task_id)
    if rules:
        if not await check_rules(recommendation.text, rules):
            logger.debug(f"User recommendation {recommendation.id} skipped due to rules")
            await delete_user_recommendation(recommendation.user_id, recommendation.id)
            logger.debug(f"User recommendation {recommendation.id} removed due to rules")
            return

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
                text=f"Предложение от {('@' + recommendation.username) or 'Unknown'}:\n> {recommendation.text}",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
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
        return
    try:
        linked = await save_user_channel(user["id"], message.chat.id)
        if linked:
            await message.answer(f"Добро пожаловать! В этот канал вам будут приходить ваши лиды")
        else:
            await message.answer(f"Ваши лиды ждут вас!")
    except Exception as e:
        logger.warning(f"Failed to link recommendations channel id: {e}")
        await bot.send_message(chat_id=message.chat.id, text=f"Ошибка во время привязки канала лидов к пользователю Cardinal. Попробуйте позже ещё раз")


@tg_router.callback_query(F.data.startswith("ra_"))
async def accept_callback(callback: CallbackQuery):
    rec_id = callback.data.split("_", 1)[1]
    try:
        await embedding.accept_recommendation(rec_id)
        await finish_recommendation(callback, rec_id)
    except Exception as e:
        logger.warning(f"Failed to accept recommendation: {e}")
        await bot.send_message(chat_id=callback.message.chat.id, text="Произошла ошибка с дообучением, попробуйте позже", reply_to_message_id=callback.message.message_id)


@tg_router.callback_query(F.data.startswith("rd_"))
async def decline_callback(callback: CallbackQuery, state: FSMContext):
    rec_id = callback.data.split("_", 1)[1]
    try:
        await embedding.decline_recommendation(rec_id)
        await bot.send_message(chat_id=callback.message.chat.id, text="В чём заключается проблема?", reply_to_message_id=callback.message.message_id)
        await state.update_data(text=callback.message.text, rec_id=rec_id)
        await state.set_state(DeclineFlow.waiting_for_user_description)
        await finish_recommendation(callback, rec_id)
    except Exception as e:
        logger.warning("Failed to decline recommendation", e)
        await bot.send_message(chat_id=callback.message.chat.id, text="Произошла ошибка с дообучением, попробуйте позже", reply_to_message_id=callback.message.message_id)


@tg_router.message(DeclineFlow.waiting_for_user_description)
async def handle_decline(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data['text']
    rec_id = data['rec_id']
    feedback = data.get('feedback')
    if not feedback:
        feedback = message.text
    else:
        feedback = feedback + ";\n" + message.text

    rules = await ai.extract_rules(text, feedback)

    try:
        if len(rules) == 1 and rules[0] == "insufficient data":
            await bot.send_message(chat_id=message.chat.id, text="Укажите более явные причины по которым стоит отклонять подобные лиды", reply_to_message_id=message.message_id)
            await state.update_data(feedback=feedback)
        else:
            recommendation = await fetch_recommendation_by_id(rec_id)
            await save_user_rules(recommendation['user_id'], recommendation['task_id'], rules)
            if len(rules) > 1:
                await message.answer("Спасибо, правила добавлены!")
            else:
                await message.answer("Спасибо, правило добавлено!")
            await state.clear()
    except Exception as e:
        logger.warning(f"Failed to extract rules for recommendations: {e}")
        await bot.send_message(chat_id=message.chat.id, text="Произошла ошибка с дообучением, попробуйте позже", reply_to_message_id=message.message_id)


@tg_router.callback_query(F.data.startswith("rg_"))
async def generate_callback(callback: CallbackQuery):
    try:
        await bot.send_message(chat_id=callback.message.chat.id, text="Функция временно недоступна", reply_to_message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to send recommendation channel id: {e}")


async def finish_recommendation(callback: CallbackQuery, rec_id: str):
    try:
        new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Сгенерировать", callback_data=f"rg_{rec_id}")
            ]
        ])
        await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=new_keyboard)
    except Exception as e:
        logger.warning(f"Failed to finish recommendation in {callback.message.chat.id}: {e}")


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

    webhook_url = os.environ["WEBHOOK_URL"]
    if webhook_url.endswith("/"):
        webhook_url = webhook_url[:-1]
    await bot.set_webhook(f"{webhook_url}/api/finder/recommendations/webhook", secret_token=os.environ["WEBHOOK_KEY"])
    logger.info(f"Telegram recommendations webhook set to {webhook_url}/api/finder/recommendations/webhook")
