from fastapi import APIRouter

from .tasks.routers import router as tasks_routers

routers = APIRouter()

routers.include_router(tasks_routers, prefix="/tasks", tags=["task-prediction"])
