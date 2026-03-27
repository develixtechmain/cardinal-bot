import logging
import os
from contextlib import asynccontextmanager
from typing import List
from uuid import UUID

import dotenv
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from starlette.responses import JSONResponse

import ai
import db
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
            await ai.init_llm()
            logger.info(f"LLM initiated.")
        except Exception as e:
            raise RuntimeError(f"Failed init LLM : {e}")

        try:
            await db.init_postgresql()
            logger.info(f"Connected to PostgreSQL.")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")

        instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info(f"Metrics enabled {os.environ.get('ENABLE_METRICS', False)}.")

        logger.info(f"AI Core started.")

        yield
    except Exception as e:
        logger.error(f"Unexpected error during lifespan: {e}")
        raise
    finally:
        await db.disconnect()
        logger.info(f"AI Core stopped.")


app = FastAPI(lifespan=lifespan, redirect_slashes=False)

app.add_middleware(security.KeyAuthMiddleware)
app.add_middleware(security.JWTAuthMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

instrumentator = Instrumentator(should_respect_env_var=True, excluded_handlers=["/metrics", "/docs", "/openapi.json"], env_var_name="ENABLE_METRICS")
instrumentator.instrument(app)


@app.exception_handler(Exception)
async def exception_handler(_: Request, e: Exception):
    logger.warning(f"Error response: {e}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(e)},
        headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
    )


class Question(BaseModel):
    question: str
    answer: str
    selections: list[str]


class CheckRulesRequest(BaseModel):
    text: str
    rules: list[str]


class RuleExtractRequest(BaseModel):
    text: str
    userText: str


@app.post("/api/onboarding/start", tags=["onboarding"], status_code=status.HTTP_201_CREATED)
async def start_onboarding(request: Request):
    user = await db.fetch_user_by_id(request.state.user_id)
    return await db.create_onboarding(user["id"])


@app.post("/api/onboarding/{onboarding_id}/answer", tags=["onboarding"])
async def answer_onboarding(request: Request, onboarding_id: UUID, questions: List[Question]):
    onboarding = await db.fetch_onboarding_by_id(request.state.user_id, onboarding_id, True)
    if onboarding["status"] == "completed":
        raise HTTPException(status_code=400, detail="Анкета уже заполнена")

    return await ai.process_answer(request.state.user_id, onboarding, questions)


@app.post("/api/onboarding/{onboarding_id}/complete", tags=["onboarding"])
async def complete_onboarding(request: Request, onboarding_id: UUID):
    onboarding = await db.fetch_onboarding_by_id(request.state.user_id, onboarding_id, True)
    if onboarding["status"] != "completed":
        raise HTTPException(status_code=400, detail="Недостаточно заполнена анкета")

    tags = await ai.get_cloud_of_meaning(onboarding["questions"])
    if len(tags) <= 5:
        await db.restart_onboarding(request.state.user_id, onboarding_id)
        raise HTTPException(status_code=400, detail="Недостаточно заполнена анкета")

    title = await ai.get_task_title(tags)

    return {"title": title, "tags": tags}


@app.post("/api/rules/check", tags=["rules"])
async def check_rules(request: CheckRulesRequest):
    if not await ai.check_rules(request.text, request.rules):
        raise HTTPException(status_code=409, detail="Not matches rules")


@app.post("/api/rules/extract", tags=["rules"])
async def extract_rules(request: RuleExtractRequest):
    return await ai.extract_rules(request.text, request.userText)


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
