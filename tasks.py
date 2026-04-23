from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskFromText, TaskRead, TaskUpdate
from app.services.nlp_parser import parse_task_text

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead)
def create_task(payload: TaskCreate, session: Session = Depends(get_session)):
    now = datetime.utcnow()
    task = Task(
        title=payload.title,
        description=payload.description,
        due_at=payload.due_at,
        created_at=now,
        updated_at=now,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.post("/from-text", response_model=TaskRead)
def create_task_from_text(payload: TaskFromText, session: Session = Depends(get_session)):
    parsed = parse_task_text(payload.text)
    now = datetime.utcnow()
    task = Task(title=parsed.title, due_at=parsed.due_at, created_at=now, updated_at=now)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.get("/", response_model=List[TaskRead])
def list_tasks(
    session: Session = Depends(get_session),
    status: Optional[TaskStatus] = Query(default=None),
):
    stmt = select(Task).order_by(Task.created_at.desc())
    if status is not None:
        stmt = stmt.where(Task.status == status)
    return session.exec(stmt).all()


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    now = datetime.utcnow()
    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.due_at is not None:
        task.due_at = payload.due_at
    if payload.status is not None:
        task.status = payload.status
        if payload.status == TaskStatus.done:
            task.completed_at = now

    task.updated_at = now
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"ok": True}

