import logging
import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import Depends, FastAPI, HTTPException, Request

from config import trace_api_key
from db import close_db, get_pool, init_db
from ingest import ingest_event_pool
from models import TraceEventIngest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def verify_trace_api_key(request: Request) -> None:
    expected = trace_api_key()
    if not expected:
        raise HTTPException(status_code=503, detail="TRACE_SERVICE_API_KEY is not configured")
    header = request.headers.get("X-Trace-API-Key") or request.headers.get("x-trace-api-key")
    if header != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Trace-API-Key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="Cardinal Trace Ingest Service", lifespan=lifespan, redirect_slashes=False)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/internal/traces/events", dependencies=[Depends(verify_trace_api_key)])
async def post_event(body: TraceEventIngest):
    pool = get_pool()
    try:
        event_id = await ingest_event_pool(pool, body)
    except asyncpg.ForeignKeyViolationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parent_event_id or correlation: {e}") from e
    except Exception as e:
        logger.exception("ingest failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"id": event_id, "correlation_id": str(body.correlation_id)}


def main():
    port = int(os.environ.get("PORT", "8010"))
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
