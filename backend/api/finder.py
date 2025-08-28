import logging
import uuid
from typing import List, Any, Optional

from fastapi import Request, APIRouter
from pydantic import BaseModel, model_validator

from bot.recommendations import send_recommendation_to_user
from db import fetch_tasks_by_user_id, fetch_user_channels_by_user_id, delete_user_channel, delete_task_by_id, patch_task_by_id, save_user_task, fetch_user_tasks_stats

router = APIRouter()
logger = logging.getLogger(__name__)


class RecommendationSendRequest(BaseModel):
    id: uuid.UUID
    user_id: str
    text: str
    username: Optional[str] = None


class CreateTaskRequest(BaseModel):
    cloud: List[str]

    # noinspection PyMethodParameters
    @model_validator(mode='before')
    def check_cloud_is_not_empty(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not 'cloud' in data:
                raise ValueError("'cloud' must be included")
            if not data['cloud']:
                raise ValueError("Cloud of meaning must contain at least one tag")
        return data


class PatchTaskRequest(BaseModel):
    active: bool


@router.get("/tasks/stats")
async def fetch_tasks_stats(request: Request):
    return await fetch_user_tasks_stats(request.state.user_id)


# TASKS
@router.get("/tasks/me")
async def fetch_tasks(request: Request):
    return await fetch_tasks_by_user_id(request.state.user_id)


@router.post("/tasks")
async def create_task(request: Request, create: CreateTaskRequest):
    return await save_user_task(request.state.user_id, create.cloud)


@router.patch("/tasks/{task_id}")
async def patch_task(request: Request, task_id: uuid.UUID, patch: PatchTaskRequest):
    return await patch_task_by_id(request.state.user_id, task_id, active=patch.active)


@router.delete("/tasks/{task_id}")
async def delete_task(request: Request, task_id: uuid.UUID):
    return await delete_task_by_id(request.state.user_id, task_id)


# RECOMMENDATIONS
@router.get("/channels/")
async def fetch_user_channels(request: Request):
    return await fetch_user_channels_by_user_id(request.state.user_id)


@router.delete("/channels/{channel_id}")
async def delete_user_channel(request: Request, channel_id: uuid.UUID):
    return await delete_user_channel(request.state.user_id, channel_id)


@router.post("/recommendations/send")
async def recommend_to_user(request: RecommendationSendRequest):
    await send_recommendation_to_user(request)
