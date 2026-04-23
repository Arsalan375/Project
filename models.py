from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    overdue = "overdue"
    rolled_over = "rolled_over"


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(index=True)
    description: Optional[str] = None

    status: TaskStatus = Field(default=TaskStatus.todo, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    due_at: Optional[datetime] = Field(default=None, index=True)
    completed_at: Optional[datetime] = Field(default=None, index=True)

    # Reminder bookkeeping (kept in DB so it survives restarts)
    last_reminded_at: Optional[datetime] = Field(default=None, index=True)
    reminder_count: int = Field(default=0)

    # Rollover bookkeeping
    original_task_id: Optional[int] = Field(default=None, index=True)
    rolled_over_from_date: Optional[str] = Field(default=None, index=True)  # YYYY-MM-DD

