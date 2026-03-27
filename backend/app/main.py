"""
AInewsroom — FastAPI Application Entry Point
AI-powered newsroom system with Editorial Intelligence
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager

from .config import settings
from .api.routes import feed, draft, brain

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Initialize DB, Redis connections, etc.
    yield
    logger.info("Shutting down AInewsroom")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## AInewsroom — Editorial Intelligence System

AI-powered newsroom system that combines speed with journalistic integrity.

### Key Features
- **Feed Heartbeat**: Real-time news aggregation with Editorial Weight Score
- **Editor Brief Intelligence**: AI summarization for fast editorial decisions
- **AI Drafting**: Content generation with style constitution awareness
- **Copyright Analysis**: 3-axis copyright risk assessment (content/style/structure)
- **Brain Maturity**: Organization-specific style learning
- **Angle Generator**: 1 news → 3-5 content angles
- **Fact Checker**: Automatic claim detection and verification guidance
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(feed.router, prefix="/api/v1")
app.include_router(draft.router, prefix="/api/v1")
app.include_router(brain.router, prefix="/api/v1")


# WebSocket manager for real-time feed updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.active_connections.remove(conn)


ws_manager = ConnectionManager()


@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """WebSocket endpoint for real-time feed updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, send pings
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "tagline": "AI ที่ไม่ใช่แค่เครื่องมือ แต่เป็นระบบที่ช่วยคิด วิเคราะห์ และป้องกันความเสี่ยง",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )
