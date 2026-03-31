import os

from dotenv import load_dotenv

load_dotenv()


def database_url_parts():
    host = os.environ.get("DB_HOST", os.environ.get("POSTGRESQL_HOST", "postgresql"))
    port = int(os.environ.get("DB_PORT", os.environ.get("POSTGRESQL_PORT", "5432")))
    user = os.environ.get("DB_USER", os.environ.get("POSTGRESQL_USER", "cardinal"))
    password = os.environ.get("DB_PASS", os.environ.get("POSTGRESQL_PASS", ""))
    database = os.environ.get("DB_NAME", os.environ.get("POSTGRESQL_DB", "cardinal"))
    return host, port, user, password, database


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
