import logging
import re
from enum import Enum
from functools import partial

from pyrogram import Client
from pyrogram.types import InlineKeyboardButton

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

tme_prefix_length = len("https://t.me/")

id_buttons = tuple(["Написать Заказчику"])
url_buttons = tuple(["Написать Заказчику", "Связаться с автором", "Откликнуться", "Написать автору"])
click_buttons = tuple(["Написать Заказчику", "Показать контакты"])

clean_regex = re.compile(r"\W+")
spam_buttons = [
    "выполнить",
    "подписался",
    "я подписался",
    "я не бот",
    "я не робот",
    "я человек",
    "не бот",
    "привет",
    "простить",
    "простить05",
    "простить15",
    "простить25",
    "простить35",
    "простить45",
    "простить55",
    "кикнуть",
    "кикнуть05",
    "кикнуть15",
    "кикнуть25",
    "кикнуть35",
    "кикнуть45",
    "кикнуть55",
    "размьютить",
    "пройти тест",
    "пройти проверку",
    "открыть правила",
    "отмена",
    "разблокировать",
    "снять ограничение",
    "разрешить мне писать",
    "открыть канал",
    "купить сейчас",
    "подробнее о заявках",
    "добавить категорию",
    "скрыть",
    "оплатить",
    "проверить подписку",
    "за что",
    "это бот",
    "бот с вакансиями",
    "жмите если понятны условия",
    "как писать в чате",
    "getclient фриланс вакансии",
    "нужное фриланс",
    "соглашаюсь с обработкой пд",
    "jobosphere фриланс чат",
    "твоя удаленка поиск работы вакансии",
    "ваше резюме предложение рекламу сюда",
    "подписаться",
    "подписаться 1",
    "подписаться на канал вакансий",
    "подписаться на канал tmeccmozadw9ig1ztfi",
    "удаленно работа и вакансии",
    "удалённо работа и вакансии",
    "бот для поиска заказов",
    "удаление отзывов wb",
    "записаться",
    "дизайнеры инфографики wb ozon",
    "фриланс вакансии удаленка",
    "форум бухгалтеров",
    "получить список фриланс чатов",
    "фриланс чат биржа вакансий",
    "фриланс чат работа",
    "фриланс вакансии ищу работу",
    "подробнее",
    "забрать инструкцию",
    "забрать деньги",
    "хочу vip статус",
    "подробности тут",
    "участвовать",
    "на карту",
    "по ссп",
    "миллион бонусов",
    "взять работу здесь",
    "играть в телеграм",
    "играть на сайте",
    "ввести промокод krov",
    "забрать бонусы",
    "забрать все подарки",
    "akses penuh",
    "full",
    "aqua play",
    "jetton",
    "lucky bear",
]

ignore_buttons = [
    "публикация вакансии резюме",
    "искать заказчиков",
    "разместить",
    "разместить вакансию",
    "разместить резюме",
    "разместить вакансию резюме",
    "разместить вакансию резюме рекламу",
    "разместить услугу резюме",
    "ℹ фриланс котэ больше заказов",
    "фриланс котэ больше заказов",
    "фриланс котэ заказы",
    "подписаться на канал",
    "сommunity котэ",
    "вакансии дизайнерам",
    "все вакансии",
    "50 вакансий в день тут",
    "наш супер чатик",
    "резервный канал с вакансиями",
    "ссылка на источник",
    "жалоба на вакансию",
    "схемы обмана",
    "smm чат",
    "заказать маркетинг",
    "найти исполнителя монтажера",
    "нейросеть на русском",
    "спам мошенничество",
    "спам",
]

spam_buttons_set = set(clean_regex.sub("", button_text.lower()) for button_text in spam_buttons)
ignore_buttons_set = set(clean_regex.sub("", button_text.lower()) for button_text in ignore_buttons)


class ButtonsHandle(str, Enum):
    SKIPPED = "skip"
    IGNORED = "ignore"
    PROCESSED = "processed"
    PROCESSED_FAST = "processed_fast"
    FAILED = "failed"


async def handle_buttons(buttons_rows: list[list[InlineKeyboardButton]], func) -> ButtonsHandle:
    buttons = 0
    ignored = 0
    for row in buttons_rows:
        for button in row:
            buttons += 1
            cleaned_text = clean_regex.sub("", button.text.lower())
            if cleaned_text in spam_buttons_set:
                return ButtonsHandle.SKIPPED
            if cleaned_text in ignore_buttons_set:
                ignored += 1
            else:
                handle = await func(button)
                if handle in (ButtonsHandle.PROCESSED_FAST, ButtonsHandle.PROCESSED):
                    return handle
    if buttons == ignored:
        return ButtonsHandle.IGNORED
    else:
        return ButtonsHandle.FAILED


async def handle_fast_url_button(button: InlineKeyboardButton, fast_name: str, app: Client, payload: dict) -> ButtonsHandle:
    if button.url and fast_name in button.text:
        logger.info(f"{app.name} | BUTTON FAST URL {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        if _extract_username_from_url(button, payload):
            return ButtonsHandle.PROCESSED_FAST
    return ButtonsHandle.FAILED


async def handle_fast_id_url_button(button: InlineKeyboardButton, fast_name: str, app: Client, payload: dict) -> ButtonsHandle:
    if fast_name in button.text:
        if await _handle_id_button(button, app, payload):
            logger.info(f"{app.name} | Button FAST ID {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
            return ButtonsHandle.PROCESSED_FAST
        elif await _handle_url_button(button, app, payload):
            logger.info(f"{app.name} | BUTTON FAST URL {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
            return ButtonsHandle.PROCESSED_FAST
        else:
            logger.warning(f"{app.name} | FAILED BUTTON FAST {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
            return ButtonsHandle.FAILED
    return ButtonsHandle.FAILED


async def handle_fast_click_button(button: InlineKeyboardButton, fast_click_name: str, fast_name: str, app: Client, payload: dict) -> ButtonsHandle:
    if fast_click_name in button.text:
        logger.info(f"{app.name} | BUTTON FAST CLICK {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        if await _click_button(button, fast_name, app, payload):
            return ButtonsHandle.PROCESSED_FAST
    elif fast_name in button.text:
        return await handle_fast_id_url_button(button, fast_name, app, payload)
    return ButtonsHandle.FAILED


async def _click_button(button: InlineKeyboardButton, fast_name: str | None, app: Client, payload: dict) -> bool:
    return await __click_button(button, True, fast_name, app, payload)


async def __click_button(button: InlineKeyboardButton, retry: bool, fast_name: str | None, app: Client, payload: dict) -> bool:
    try:
        logger.debug(f"{app.name} | BUTTON click {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        await app.request_callback_answer(chat_id=payload["chat_id"], message_id=payload["message_id"], timeout=5, callback_data=button.callback_data)
    except Exception as e:
        return False

    try:
        logger.info(f"{app.name} | BUTTON update {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        message = await app.get_messages(payload["chat_id"], payload["message_id"])
        if message.reply_markup is None:
            raise Exception(f"BUTTON click failed: no reply markup after update {message}")
        else:
            new_buttons_rows = message.reply_markup.inline_keyboard
    except Exception as e:
        logger.warning(f"Failed to update message buttons {button.text} from {payload['chat_username']}: {e}")
        return False

    if fast_name:
        found = await handle_buttons(new_buttons_rows, partial(handle_fast_id_url_button, fast_name=fast_name, app=app, payload=payload))
    else:
        found = await handle_buttons(new_buttons_rows, partial(_handle_id_url_button, app=app, payload=payload))

    if found:
        return True
    else:
        raise Exception(f"""
            Failed to process click button:
            Click Button: chat {payload['chat_username']} {button.text}: url {button.url} webapp {button.web_app} callback {button.callback_data}
            New Buttons: {new_buttons_rows}
            """)


async def handle_generic_button(button: InlineKeyboardButton, app: Client, payload: dict) -> ButtonsHandle:
    if await _handle_generic_button(button, app, payload):
        return ButtonsHandle.PROCESSED
    else:
        return ButtonsHandle.FAILED


async def _handle_generic_button(button: InlineKeyboardButton, app: Client, payload: dict) -> bool:
    if button.url and any(text in button.text for text in url_buttons):
        return await _handle_url_button(button, app, payload)
    elif button.user_id and any(text in button.text for text in id_buttons):
        return await _handle_id_button(button, app, payload)
    elif any(text in button.text for text in click_buttons):
        logger.info(f"{app.name} | Button SLOW CLICK {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        return await _click_button(button, None, app, payload)
    else:
        logger.info(f"{app.name} | Button SLOW NEW: {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        return False


async def _handle_id_url_button(button: InlineKeyboardButton, app: Client, payload: dict):
    if await _handle_id_button(button, app, payload):
        logger.info(f"{app.name} | Button SLOW ID {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        return True
    elif await _handle_url_button(button, app, payload):
        logger.info(f"{app.name} | BUTTON SLOW URL {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        return True
    else:
        logger.warning(f"{app.name} | FAILED BUTTON SLOW {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        return False


async def _handle_url_button(button: InlineKeyboardButton, app: Client, payload: dict) -> bool:
    if button.url and any(text in button.text for text in url_buttons):
        logger.info(f"{app.name} | Button SLOW URL {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        return _extract_username_from_url(button, payload)
    return False


def _extract_username_from_url(button: InlineKeyboardButton, payload: dict) -> bool:
    payload["user_username"] = button.url[tme_prefix_length:]
    return True


async def _handle_id_button(button: InlineKeyboardButton, app: Client, payload: dict) -> bool:
    if button.user_id:
        logger.info(f"{app.name} | Button SLOW ID {button.text}: chat {payload['chat_username']} url {button.url} webapp {button.web_app} callback {button.callback_data} user_id {button.user_id}")
        return await _extract_username_by_id(button, app, payload)
    return False


async def _extract_username_by_id(button: InlineKeyboardButton, app: Client, payload: dict) -> bool:
    payload["user_id"] = button.user_id
    user = await app.get_users(button.user_id)
    payload["user_username"] = user.username
    return True
