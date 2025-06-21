import os


def validate_env(env):
    if not os.environ[env]:
        raise ValueError(f"Переменная окружения '{env}' не установлена или пуста!")
