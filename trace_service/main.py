import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request

from config import trace_api_key
from db import close_db, get_pool, init_db
from ingest import ingest_event_pool
from models import TraceEventIngest
from queue import close_queue, init_queue, publish, run_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_worker_task: asyncio.Task | None = None


async def _ingest_from_queue(body: dict) -> None:
    """Called by the worker for each message consumed from RabbitMQ."""
    event = TraceEventIngest.model_validate(body)
    await ingest_event_pool(get_pool(), event)


def verify_trace_api_key(request: Request) -> None:
    expected = trace_api_key()
    if not expected:
        raise HTTPException(status_code=503, detail="TRACE_SERVICE_API_KEY is not configured")
    header = request.headers.get("X-Trace-API-Key") or request.headers.get("x-trace-api-key")
    if header != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Trace-API-Key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _worker_task
    await init_db()
    await init_queue()
    _worker_task = asyncio.create_task(run_worker(_ingest_from_queue))
    yield
    _worker_task.cancel()
    try:
        await _worker_task
    except asyncio.CancelledError:
        pass
    await close_queue()
    await close_db()


app = FastAPI(title="Cardinal Trace Ingest Service", lifespan=lifespan, redirect_slashes=False)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/internal/traces/events", dependencies=[Depends(verify_trace_api_key)])
async def post_event(body: TraceEventIngest):
    try:
        await publish(body.model_dump(mode="json"))
    except Exception as e:
        logger.exception("failed to enqueue trace event")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"queued": True, "correlation_id": str(body.correlation_id)}


def main():
    port = int(os.environ.get("PORT", "8010"))
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
