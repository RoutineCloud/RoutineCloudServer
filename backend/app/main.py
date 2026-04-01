from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Create FastAPI app
app = FastAPI(title="Routine Cloud API Gateway")


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
from app.api.runtime import router as runtime_router
from app.api.admin import router as admin_router
from app.api.friends import router as friends_router

# Create sub-app for versioning
v1 = FastAPI(title="Routine Cloud API v1", version="1.0.0")

# Apply common exception handlers to sub-apps
v1.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Include routers in sub-apps
v1.include_router(device_router)
v1.include_router(user_router)
v1.include_router(task_router)
v1.include_router(routine_router)
v1.include_router(runtime_router)
v1.include_router(admin_router)
v1.include_router(friends_router)

# Mount sub-app to the main gateway
app.mount("/v1", v1)

@app.get("/")
async def root():
    return {"message": "Welcome to Routine Cloud API Gateway"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
