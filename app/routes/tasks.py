from fastapi import APIRouter, HTTPException
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskQuery
from typing import Dict, Any

router = APIRouter()

@router.post("/query")
async def query_tasks(task_query: TaskQuery) -> Dict[str, Any]:
    """
    Handle a natural language query for tasks.
    """
    try:
        if not task_query.question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        results = await TaskService.query_tasks(task_query.question)
        
        if not results["results"]:
            return {
                "message": "No tasks found matching your query.",
                "query": results["query"],
                "results": []
            }
            
        return {
            "message": "Query executed successfully",
            "query": results["query"],
            "response": results["response"],
            "results": results["results"],
            "count": results["count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def add_task(task: TaskCreate):
    """
    Add a new task.
    """
    try:
        task_id = await TaskService.add_task(task)
        return {
            "message": "Task added successfully",
            "task_id": task_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))