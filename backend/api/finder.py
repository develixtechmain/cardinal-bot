import datetime
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from bot.recommendations import send_recommendation_to_user
from service.finder import delete_task_by_id, fetch_tasks_by_user_id, fetch_user_tasks_stats, patch_task_by_id, save_user_task

router = APIRouter()
logger = logging.getLogger(__name__)


class RecommendationSendRequest(BaseModel):
    id: uuid.UUID
    user_id: str
    task_id: uuid.UUID
    text: str
    username: Optional[str] = None
    message_created_at: datetime.datetime
    correlation_id: Optional[uuid.UUID] = None


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    cloud: list[str] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def title_must_not_be_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty or whitespace")
        return v


class PatchTaskRequest(BaseModel):
    title: Optional[str] = None
    active: Optional[bool] = None


@router.get("/tasks/stats")
async def fetch_tasks_stats(request: Request):
    return await fetch_user_tasks_stats(request.state.user_id)


# TASKS
@router.get("/tasks/me")
async def fetch_tasks(request: Request):
    return await fetch_tasks_by_user_id(request.state.user_id)


@router.post("/tasks")
async def create_task(request: Request, create: CreateTaskRequest):
    return await save_user_task(request.state.user_id, create.title, create.cloud)


@router.patch("/tasks/{task_id}")
async def patch_task(request: Request, task_id: uuid.UUID, patch: PatchTaskRequest):
    return await patch_task_by_id(request.state.user_id, task_id, patch)


@router.delete("/tasks/{task_id}")
async def delete_task(request: Request, task_id: uuid.UUID):
    return await delete_task_by_id(request.state.user_id, task_id)


# RECOMMENDATIONS
@router.post("/recommendations/send")
async def recommend_to_user(http_request: Request, body: RecommendationSendRequest):
    hdr = http_request.headers.get("X-Correlation-ID") or http_request.headers.get("x-correlation-id")
    if hdr and not body.correlation_id:
        try:
            body = body.model_copy(update={"correlation_id": uuid.UUID(hdr.strip())})
        except ValueError:
            pass
    return await send_recommendation_to_user(body)
