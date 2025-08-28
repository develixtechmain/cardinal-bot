import logging
from contextlib import asynccontextmanager
from typing import List
from uuid import UUID

import dotenv
import uvicorn
from fastapi import Request, FastAPI, HTTPException, status
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

import ai
import db
import embedding
import security

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_):
    logger.info("AI Core startup initiated.")

    try:
        dotenv.load_dotenv()

        try:
            security.init_security()
        except Exception as e:
            raise RuntimeError(f"Failed to configure security: {e}")

        try:
            embedding.init_embedding()
        except Exception as e:
            raise RuntimeError(f"Failed to configure embedding: {e}")

        try:
            await ai.init_llm()
            logger.info(f"LLM initiated.")
        except Exception as e:
            raise RuntimeError(f"Failed init LLM : {e}")

        try:
            await db.init_postgresql()
            logger.info(f"Connected to PostgreSQL.")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")

        logger.info(f"AI Core started.")

        yield
    except Exception as e:
        logger.error(f"Unexpected error during lifespan: {e}")
        raise
    finally:
        await db.disconnect()
        logger.info(f"AI Core stopped.")


app = FastAPI(lifespan=lifespan)

app.middleware("http")(security.jwt_auth_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    question: str
    answer: str


@app.post("/api/onboarding/start", status_code=status.HTTP_201_CREATED)
async def start_onboarding(request: Request):
    user = await db.fetch_user_by_id(request.state.user_id)
    return await db.create_onboarding(user['id'])


@app.post("/api/onboarding/{onboarding_id}/answer")
async def answer_onboarding(request: Request, onboarding_id: UUID, questions: List[Question]):
    onboarding = await db.fetch_onboarding_by_id(request.state.user_id, onboarding_id, True)
    if onboarding['status'] == 'completed':
        raise HTTPException(status_code=400, detail="Анкета уже заполнена")

    return await ai.process_answer(request.state.user_id, onboarding, questions)


@app.post("/api/onboarding/{onboarding_id}/complete")
async def complete_onboarding(request: Request, onboarding_id: UUID):
    onboarding = await db.fetch_onboarding_by_id(request.state.user_id, onboarding_id, True)
    if onboarding['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Недостаточно заполнена анкета")

    tags = await ai.get_cloud_of_meaning(onboarding['questions'])

    await db.delete_onboarding_by_id(request.state.user_id, onboarding_id)
    return tags


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
