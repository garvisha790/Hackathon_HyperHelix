import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

from app.config import get_settings
from app.api.router import api_router

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "pipeline.log"
_fmt = logging.Formatter("%(asctime)s %(levelname)-8s [%(name)s] %(message)s", datefmt="%H:%M:%S")

_stream_handler = logging.StreamHandler(sys.stderr)
_stream_handler.setLevel(logging.INFO)
_stream_handler.setFormatter(_fmt)

_handlers: list[logging.Handler] = [_stream_handler]
try:
    _file_handler = logging.FileHandler(str(_LOG_FILE), mode="a", encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(_fmt)
    _handlers.append(_file_handler)
except OSError:
    pass  # Container may not have writable log dir; stderr is sufficient

logging.basicConfig(level=logging.INFO, handlers=_handlers, force=True)
logging.getLogger("app").setLevel(logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

settings = get_settings()


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(
        settings.redis_url, encoding="utf-8", decode_responses=True
    )

    # Reset any documents stuck in PROCESSING from a previous crash
    from app.database import async_session
    from app.models.document import Document
    from sqlalchemy import update
    async with async_session() as session:
        result = await session.execute(
            update(Document)
            .where(Document.status == "PROCESSING")
            .values(status="UPLOADED")
            .returning(Document.id)
        )
        stuck = result.all()
        if stuck:
            await session.commit()
            logger.warning(f"[STARTUP] Reset {len(stuck)} stuck documents from PROCESSING -> UPLOADED")
        else:
            logger.info("[STARTUP] No stuck documents found")

    yield
    await app.state.redis.close()


app = FastAPI(
    title="Digital CA API",
    description="AI-powered Digital Chartered Accountant for Indian Businesses",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "digital-ca"}
