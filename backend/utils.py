import os
import re
from datetime import datetime, timezone


def validate_env(env):
    if not os.environ[env]:
        raise ValueError(f"Переменная окружения '{env}' не установлена или пуста!")


escape_regex = re.compile(r"([._*()[\]~`>#+\-=|{}!])")


def escape_markdown_v2(text):
    return escape_regex.sub(r"\\\1", text)


def data_to_update_query(data: dict, first_param: int):
    if not data:
        return None, None

    update_fields = list(data.keys())
    update_values = list(data.values())

    query_part = [f"{field} = ${i + first_param}" for i, field in enumerate(update_fields)]
    return ", ".join(query_part), update_values


def is_subscription_expired(subscription):
    now = datetime.now(timezone.utc)
    trial_end = subscription["trial_ends_at"]
    subscription_end = subscription["subscription_ends_at"]

    if trial_end is not None and subscription_end is not None:
        latest_end = max(trial_end, subscription_end)
        return now > latest_end
    elif trial_end is not None:
        return now > trial_end
    elif subscription_end is not None:
        return now > subscription_end
    else:
        return True
