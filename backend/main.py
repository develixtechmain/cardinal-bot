import asyncio
import logging.config
import os
from contextlib import asynccontextmanager

import dotenv
import uvicorn
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.cors import CORSMiddleware

import ai
import bot
import embedding
import lava
from api import *
from api import security
from bot import *
from db import init_postgresql, disconnect, check_transactions

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

tasks = [check_transactions]
tasksFutures = []


@asynccontextmanager
async def lifespan(_):
    logger.info("AI Core startup initiated.")

    try:
        dotenv.load_dotenv()

        try:
            security.init_security()
        except Exception as e:
            raise RuntimeError(f"Failed to configure security") from e

        try:
            ai.init_ai()
        except Exception as e:
            raise RuntimeError(f"Failed to configure ai core") from e

        try:
            embedding.init_embedding()
        except Exception as e:
            raise RuntimeError(f"Failed to configure embedding") from e

        try:
            lava.init_lava()
        except Exception as e:
            raise RuntimeError(f"Failed to configure lava") from e

        try:
            await bot.init_core_webhook()
        except Exception as e:
            raise RuntimeError(f"Failed to configure core bot") from e

        try:
            await bot.init_recommendations_webhook()
        except Exception as e:
            raise RuntimeError(f"Failed to configure recommendations bot") from e

        try:
            await init_postgresql()
            logger.info(f"Connected to PostgreSQL.")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL") from e

        instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info(f"Metrics enabled {os.environ.get('ENABLE_METRICS', False)}.")

        for i, task in enumerate(tasks):
            tasksFutures.append(asyncio.create_task(task()))
            logger.info(f"Task {i} started.")
        logger.info(f"Backend Core started.")
        yield
    except Exception as e:
        logger.error(f"Unexpected error during lifespan: {e}")
        raise
    finally:
        for i, task in enumerate(tasksFutures):
            task.cancel()
            try:
                await task
                print(f"Task {i} finished successfully.")
            except asyncio.CancelledError:
                print(f"Task {i} cancelled gracefully.")

        await disconnect()

        await embedding.stop_embedding()
        await ai.stop_ai()
        await lava.stop_lava()

        logger.info(f"Backend Core stopped.")


app = FastAPI(lifespan=lifespan)

app.middleware("http")(security.key_auth_middleware)
app.middleware("http")(security.webhook_auth_middleware)
app.middleware("http")(security.jwt_auth_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(core_webhook_router, prefix="/api", tags=["webhook"])
app.include_router(finder_router, prefix="/api/finder", tags=["finder"])
app.include_router(recommendations_webhook_router, prefix="/api/finder/recommendations", tags=["webhook"])
app.include_router(subscription_router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(refs_router, prefix="/api/refs", tags=["refs"])
app.include_router(refs_redirect_router, prefix="/r", tags=["refs_redirect"])

instrumentator = Instrumentator(
    should_respect_env_var=True,
    excluded_handlers=["/metrics", "/docs", "/openapi.json"],
    env_var_name="ENABLE_METRICS",
)
instrumentator.instrument(app)


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
