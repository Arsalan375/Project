from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[datetime] = None


class TaskFromText(BaseModel):
    text: str = Field(..., description='Example: "submit assignment tomorrow 9am"')


class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    original_task_id: Optional[int]
    rolled_over_from_date: Optional[str]

