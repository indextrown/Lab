from fastapi import FastAPI
from app.controllers.home_controller import router as home_router
from app.controllers.profile_controller import router as profile_router

app = FastAPI(
    title="My FastAPI Docs",
    description="This is a sample FastAPI application.",
    version="1.0.0"
)

app.include_router(home_router)
app.include_router(profile_router)
