import os

from dotenv import load_dotenv

load_dotenv()


def trace_api_key() -> str:
    return os.environ.get("TRACE_SERVICE_API_KEY", "")


def database_url_parts():
    """Dedicated trace DB (trace-postgresql), separate from main cardinal DB."""
    host = os.environ.get("TRACE_DB_HOST", "trace-postgresql")
    port = int(os.environ.get("TRACE_DB_PORT", "5432"))
    user = os.environ.get("TRACE_DB_USER", "trace")
    password = os.environ.get("TRACE_DB_PASS", "")
    database = os.environ.get("TRACE_DB_NAME", "trace")
    return host, port, user, password, database
