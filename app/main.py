from fastapi import FastAPI
from app.routes.tasks import router as tasks_router

app = FastAPI()

# Add routes
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
