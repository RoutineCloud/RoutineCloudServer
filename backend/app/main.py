from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin, ModelView
from app.db.session import engine
from app.db import base as models_base

# Create FastAPI app
app = FastAPI(title="Routine Cloud API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #TODO In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import API routers
from app.api.auth import router as auth_router
from app.api.device import router as device_router
from app.api.user import router as user_router
from app.api.oauth import router as oauth_router
from app.api.task import router as task_router
from app.api.routine import router as routine_router

# Include API routers

admin = Admin(app, engine)

class UserAdmin(ModelView, model=models_base.User):
    column_list = [models_base.User.id, models_base.User.username]

admin.add_view(UserAdmin)
app.include_router(auth_router)
app.include_router(device_router)
app.include_router(user_router)
app.include_router(oauth_router)
app.include_router(task_router)
app.include_router(routine_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Routine Cloud API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
