import uuid
from contextlib import asynccontextmanager
from typing import List
from uuid import UUID

import dotenv
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

import ai
import db
import embedding


@asynccontextmanager
async def lifespan(app):
    print("AI Core startup initiated.")

    try:
        dotenv.load_dotenv()

        try:
            await db.init_postgresql()
            print(f"Connected to PostgreSQL.")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")

        try:
            await ai.init_llm()
            print(f"LLM initiated.")
        except Exception as e:
            raise RuntimeError(f"Failed init LLM : {e}")

        try:
            embedding.init_embedding()
        except Exception as e:
            raise RuntimeError(f"Failed to configure: {e}")

        print(f"AI Core started.")

        yield
    except Exception as e:
        print(f"Unexpected error during lifespan: {e}")
        raise
    finally:
        await db.disconnect()
        print(f"AI Core stopped.")


app = FastAPI(lifespan=lifespan)


class OnboardingStartRequest(BaseModel):
    user_id: uuid.UUID


class Question(BaseModel):
    question: str
    answer: str


@app.post("/api/onboarding/start", status_code=status.HTTP_201_CREATED)
async def start_onboarding(request: OnboardingStartRequest):
    user = await db.fetch_user_by_id(request.user_id)
    return await db.create_onboarding(user['id'])


@app.post("/api/onboarding/{onboarding_id}/answer")
async def answer_onboarding(onboarding_id: UUID, questions: List[Question]):
    onboarding = await db.fetch_onboarding_by_id(onboarding_id, True)
    if onboarding['status'] == 'completed':
        raise HTTPException(status_code=400, detail="Анкета уже заполнена")

    return await ai.process_answer(onboarding, questions)


@app.post("/api/onboarding/{onboarding_id}/complete")
async def complete_onboarding(onboarding_id: UUID):
    onboarding = await db.fetch_onboarding_by_id(onboarding_id, True)
    if onboarding['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Недостаточно заполнена анкета")

    tags = await ai.get_cloud_of_meaning(onboarding['questions'])

    await db.delete_onboarding_by_id(onboarding_id)
    return tags


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
