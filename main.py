from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import engine, Base

from backend.routers import auth
from backend.routers import users
from backend.routers import news
from backend.routers import digest
from backend.routers import events

from backend.services.scheduler import (
    start_scheduler,
    stop_scheduler,
)


# =========================================================
# App Lifespan
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    # -----------------------------------------
    # Create Database Tables
    # -----------------------------------------

    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )

    # -----------------------------------------
    # Start Scheduler
    # -----------------------------------------

    scheduler = await start_scheduler()

    print("✅ Scheduler started")

    yield

    # -----------------------------------------
    # Shutdown
    # -----------------------------------------

    await stop_scheduler(scheduler)

    print("🛑 Scheduler stopped")


# =========================================================
# FastAPI App
# =========================================================

app = FastAPI(
    title="AI News Digest API",
    description="Scrapes, ranks, and delivers AI news digests",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Routers
# =========================================================

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"],
)

app.include_router(
    users.router,
    prefix="/api/users",
    tags=["Users"],
)

app.include_router(
    news.router,
    prefix="/api/news",
    tags=["News"],
)

app.include_router(
    digest.router,
    prefix="/api/digest",
    tags=["Digest"],
)
app.include_router(
    events.router,
    prefix="/api/events",
    tags=["Events"],
)



# =========================================================
# Health Check
# =========================================================

@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "service": "AI News Digest"
    }


# =========================================================
# Root
# =========================================================

@app.get("/")
async def root():

    return {
        "message": "AI News Digest API Running"
    }