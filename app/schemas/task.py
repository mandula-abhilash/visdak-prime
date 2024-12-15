from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str
    category: str

class TaskQuery(BaseModel):
    question: str
