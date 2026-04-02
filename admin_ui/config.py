import os

from dotenv import load_dotenv

load_dotenv()


def database_url_parts():
    """Dedicated trace DB (trace-postgresql), separate from main cardinal DB."""
    host = os.environ.get("TRACE_DB_HOST", "trace-postgresql")
    port = int(os.environ.get("TRACE_DB_PORT", "5432"))
    user = os.environ.get("TRACE_DB_USER", "trace")
    password = os.environ.get("TRACE_DB_PASS", "")
    database = os.environ.get("TRACE_DB_NAME", "trace")
    return host, port, user, password, database


def main_database_url_parts():
    """Main cardinal DB (postgresql), for user/subscription/payment data."""
    host = os.environ.get("MAIN_DB_HOST", "postgresql")
    port = int(os.environ.get("MAIN_DB_PORT", "5432"))
    user = os.environ.get("MAIN_DB_USER", "cardinal")
    password = os.environ.get("MAIN_DB_PASS", "")
    database = os.environ.get("MAIN_DB_NAME", "cardinal")
    return host, port, user, password, database


def bot_token() -> str:
    return os.environ.get("BOT_TOKEN", "")


def admin_login() -> str:
    return os.environ.get("ADMIN_LOGIN", "admin")


def admin_password() -> str:
    return os.environ.get("ADMIN_PASSWORD", "")


def jwt_secret() -> str:
    secret = os.environ.get("ADMIN_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("ADMIN_JWT_SECRET env var is required")
    return secret


def jwt_expiry_hours() -> int:
    return int(os.environ.get("ADMIN_JWT_EXPIRY_HOURS", "24"))
