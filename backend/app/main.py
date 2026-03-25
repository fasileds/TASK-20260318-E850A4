from fastapi import FastAPI, Request
import asyncio
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.funding import router as funding_router
from app.api.materials import router as materials_router
from app.api.registrations import router as registrations_router
from app.api.reviews import router as reviews_router
from app.api.system import router as system_router
import app.models.entities  # noqa: F401
import app.models.system  # noqa: F401
from app.bootstrap import seed_users
from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import now_utc
from app.models.entities import AccessAuditLog
from app.core.database import SessionLocal
from app.services.scheduler import daily_backup_scheduler, quality_metrics_scheduler
quality_scheduler_task: asyncio.Task | None = None
backup_scheduler_task: asyncio.Task | None = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global quality_scheduler_task, backup_scheduler_task
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()
    if settings.enable_quality_scheduler and (quality_scheduler_task is None or quality_scheduler_task.done()):
        quality_scheduler_task = asyncio.create_task(quality_metrics_scheduler())
    
    if backup_scheduler_task is None or backup_scheduler_task.done():
        backup_scheduler_task = asyncio.create_task(daily_backup_scheduler())
    
    yield
    
    # Shutdown logic
    if quality_scheduler_task is not None:
        quality_scheduler_task.cancel()
        try:
            await quality_scheduler_task
        except asyncio.CancelledError:
            pass
        quality_scheduler_task = None
    
    if backup_scheduler_task is not None:
        backup_scheduler_task.cancel()
        try:
            await backup_scheduler_task
        except asyncio.CancelledError:
            pass
        backup_scheduler_task = None


app = FastAPI(title="Activity Registration and Funding Audit Management Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    response = await call_next(request)
    auth_header = request.headers.get("Authorization")
    username = None
    if auth_header and auth_header.startswith("Bearer "):
        from app.core.crypto import decrypt_config_value
        try:
            token = auth_header.split(" ")[1]
            username = decrypt_config_value(token)
        except Exception:
            pass

    db = SessionLocal()
    try:
        db.add(
            AccessAuditLog(
                username=username,
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None,
                created_at=now_utc(),
            )
        )
        db.commit()
    finally:
        db.close()
    return response


app.include_router(auth_router)
app.include_router(registrations_router)
app.include_router(materials_router)
app.include_router(reviews_router)
app.include_router(funding_router)
app.include_router(system_router)
