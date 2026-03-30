import os

from dotenv import load_dotenv

load_dotenv()


def trace_api_key() -> str:
    return os.environ.get("TRACE_SERVICE_API_KEY", "")


def database_url_parts():
    """Same env names as backend/message_processor for one PostgreSQL."""
    host = os.environ.get("DB_HOST", os.environ.get("POSTGRESQL_HOST", "postgresql"))
    port = int(os.environ.get("DB_PORT", os.environ.get("POSTGRESQL_PORT", "5432")))
    user = os.environ.get("DB_USER", os.environ.get("POSTGRESQL_USER", "cardinal"))
    password = os.environ.get("DB_PASS", os.environ.get("POSTGRESQL_PASS", ""))
    database = os.environ.get("DB_NAME", os.environ.get("POSTGRESQL_DB", "cardinal"))
    return host, port, user, password, database
