from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.texts import BUTTON_ABOUT, BUTTON_BACK, BUTTON_DOCS, BUTTON_MANUAL_SUPPORT, BUTTON_OPEN, BUTTON_QUICKSTART, BUTTON_SUBSCRIPTION, BUTTON_SUPPORT, BUTTON_TRIAL, BUTTON_TRIAL_WITH_LOCK

CARDINAL_APP = "https://app.cardinal-x.online"
CARDINAL_CORE_START = "https://t.me/CardinalAPP_bot?start="
CARDINAL_RECOMMENDATIONS_START = "https://t.me/cardinal_leadfinder_bot?start="

CARDINAL_APP_PURCHASE = "https://app.cardinal-x.online/subscription/purchase/"
CARDINAL_SUPPORT = "https://t.me/cardinal_support_bot"
CARDINAL_DOCS = "https://cardinalx.gitbook.io"
CARDINAL_PUBLIC_OFFER = "https://app.cardinal-x.online/docs/public_offer.doc"

CARDINAL_VIDEO = "BAACAgIAAxkBAAIBXGmbeUxqa1Xu2kCZ2G3JHxMHc4wMAAJimgACRunYSAZOjot9CAsYOgQ"

CARDINAL_CORE_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text=BUTTON_QUICKSTART, callback_data="quickstart")],
        [InlineKeyboardButton(text=BUTTON_SUBSCRIPTION, callback_data="subscription")],
        [InlineKeyboardButton(text=BUTTON_DOCS, url=CARDINAL_DOCS)],
        [InlineKeyboardButton(text=BUTTON_SUPPORT, url=CARDINAL_SUPPORT)],
        [InlineKeyboardButton(text=BUTTON_ABOUT, callback_data="about_video")],
    ]
)
ABOUT_VIDEO_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text=BUTTON_DOCS, url=CARDINAL_DOCS)],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="about_video_back")],
    ]
)
ABOUT_VIDEO_BUTTONS_FIRST: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text=BUTTON_TRIAL_WITH_LOCK, callback_data="about_video_trial")],
        [InlineKeyboardButton(text=BUTTON_DOCS, url=CARDINAL_DOCS)],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="about_video_back")],
    ]
)

QUICKSTART_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text="▶️ Смотреть видео “Как получить первый результат”", callback_data="quickstart_video")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="quickstart_back")],
    ]
)
QUICKSTART_BUTTONS_FIRST: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Смотреть видео “CardinalX быстрый старт”", callback_data="quickstart_video")],
        [InlineKeyboardButton(text=BUTTON_TRIAL_WITH_LOCK, callback_data="quickstart_trial")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="quickstart_back")],
    ]
)
QUICKSTART_VIDEO_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text=BUTTON_DOCS, url=CARDINAL_DOCS)],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="quickstart_video_back")],
    ]
)
QUICKSTART_VIDEO_BUTTONS_FIRST: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text=BUTTON_TRIAL_WITH_LOCK, callback_data="quickstart_video_trial")],
        [InlineKeyboardButton(text=BUTTON_DOCS, url=CARDINAL_DOCS)],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="quickstart_video_back")],
    ]
)

SUBSCRIPTION_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_TRIAL_WITH_LOCK, callback_data="subscription_trial")],
        [InlineKeyboardButton(text="💼 Выбрать тариф", callback_data="subscription_select")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="subscription_back")],
    ]
)
SUBSCRIPTION_BUTTONS_FIRST: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_TRIAL, callback_data="subscription_trial")],
        [InlineKeyboardButton(text="💼 Посмотреть тарифы", callback_data="subscription_select")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="subscription_back")],
    ]
)
SUBSCRIPTION_TRIAL_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text=BUTTON_QUICKSTART, callback_data="quickstart")],
        [InlineKeyboardButton(text=BUTTON_SUBSCRIPTION, callback_data="subscription")],
        [InlineKeyboardButton(text=BUTTON_DOCS, url=CARDINAL_DOCS)],
        [InlineKeyboardButton(text=BUTTON_SUPPORT, url=CARDINAL_SUPPORT)],
    ]
)

SUBSCRIPTION_SELECT_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🟣 1 месяц — 4 900 ₽", web_app=WebAppInfo(url=f"{CARDINAL_APP_PURCHASE}1"))],
        [InlineKeyboardButton(text="🟣 3 месяца — 12 500 ₽", web_app=WebAppInfo(url=f"{CARDINAL_APP_PURCHASE}3"))],
        [InlineKeyboardButton(text="🟣 12 месяцев — 42 000 ₽", web_app=WebAppInfo(url=f"{CARDINAL_APP_PURCHASE}12"))],
        [InlineKeyboardButton(text="📄 Условия и оферта", url=CARDINAL_PUBLIC_OFFER)],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="subscription")],
    ]
)

SUBSCRIPTION_SELECT_BUTTONS_NO_BACK: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🟣 1 месяц — 4 900 ₽", web_app=WebAppInfo(url=f"{CARDINAL_APP_PURCHASE}1"))],
        [InlineKeyboardButton(text="🟣 3 месяца — 12 500 ₽", web_app=WebAppInfo(url=f"{CARDINAL_APP_PURCHASE}3"))],
        [InlineKeyboardButton(text="🟣 12 месяцев — 42 000 ₽", web_app=WebAppInfo(url=f"{CARDINAL_APP_PURCHASE}12"))],
        [InlineKeyboardButton(text="📄 Условия и оферта", url=CARDINAL_PUBLIC_OFFER)],
    ]
)

SUBSCRIPTION_EXPIRED_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BUTTON_SUBSCRIPTION, callback_data="subscription")]])

PURCHASE_DONE_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))]])
PURCHASE_DONE_BUTTONS_FIRST: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text=BUTTON_MANUAL_SUPPORT, url=CARDINAL_SUPPORT)], [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))]]
)

PURCHASE_FAILED_BUTTONS: InlineKeyboardMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_SUBSCRIPTION, callback_data="subscription")],
        [InlineKeyboardButton(text=BUTTON_OPEN, web_app=WebAppInfo(url=CARDINAL_APP))],
        [InlineKeyboardButton(text=BUTTON_SUPPORT, url=CARDINAL_SUPPORT)],
    ]
)

FIRST_BRIEFING_COMPLETED_BUTTONS = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🦅Активировать бота рассылщика", url=CARDINAL_RECOMMENDATIONS_START)]])
NOT_CARDINAL_USER_BUTTONS = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Перейти в главного бота", url=CARDINAL_CORE_START)]])
NO_CORE_CHANNEL_BUTTONS = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Привязать", url=CARDINAL_CORE_START)]])
