from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqladmin import Admin, ModelView
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.oauth2 import config_oauth
from app.db import base as models_base
from app.db.session import engine

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
    allow_origins=["*"],  #TODO In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import API routers
from app.api.device import router as device_router
from app.api.user import router as user_router
from app.api.oauth2 import router as oauth_router
from app.api.task import router as task_router
from app.api.routine import router as routine_router
from app.api.admin import router as admin_router
from app.websocket.routes import router as ws_router

# Include API routers

admin = Admin(app, engine)

class UserAdmin(ModelView, model=models_base.User):
    column_list = [models_base.User.id, models_base.User.username]

config_oauth(app)

admin.add_view(UserAdmin)
app.include_router(device_router)
app.include_router(user_router)
app.include_router(oauth_router)
app.include_router(task_router)
app.include_router(routine_router)
app.include_router(admin_router)
app.include_router(ws_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Routine Cloud API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
