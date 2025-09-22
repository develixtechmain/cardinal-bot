from enum import Enum


class TransactionStatus(str, Enum):
    TEMPLATE = "template"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TransactionPayment(str, Enum):
    LAVA = "lava"
    ALPHA = "alpha"
    BALANCE = 'balance'


class SubscriptionPeriod(int, Enum):
    ONE_MONTH = 1
    THREE_MONTHS = 3
    TWELVE_MONTHS = 12

    @property
    def price(self):
        prices = {
            SubscriptionPeriod.ONE_MONTH: 4900,
            SubscriptionPeriod.THREE_MONTHS: 12500,
            SubscriptionPeriod.TWELVE_MONTHS: 42000
        }
        return prices[self]


def get_price_by_months(months):
    try:
        period = SubscriptionPeriod(months)
        return period.price
    except ValueError:
        raise ValueError(f"Unexpected {months} months for init purchase")


def get_months_by_price(price):
    for period in SubscriptionPeriod:
        if period.price == price:
            return period.value
    raise ValueError(f"Unexpected {price} price for subscription prolong")
