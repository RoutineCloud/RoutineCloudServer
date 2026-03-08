from app.core.config import settings
from app.db import base as models_base
from app.db.session import engine
from app.socketio.server import sio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqladmin import Admin, ModelView
from starlette.exceptions import HTTPException as StarletteHTTPException

# Create FastAPI app
app = FastAPI(title="Routine Cloud API")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    body = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=exc.headers or {},
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).rstrip("/") for origin in settings.ALLOW_ORIGINS] if settings.ALLOW_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import API routers
from app.api.device import router as device_router
from app.api.user import router as user_router
from app.api.task import router as task_router
from app.api.routine import router as routine_router
from app.api.routine_control import router as routine_control_router
from app.api.admin import router as admin_router

admin = Admin(app, engine)


class UserAdmin(ModelView, model=models_base.User):
    column_list = [models_base.User.id, models_base.User.username]


admin.add_view(UserAdmin)
app.include_router(device_router)
app.include_router(user_router)
app.include_router(task_router)
app.include_router(routine_router)
app.include_router(routine_control_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "Welcome to Routine Cloud API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


sio.integrate(app)
