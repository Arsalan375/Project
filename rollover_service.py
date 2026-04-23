from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlmodel import Session, select

from app.models import Task, TaskStatus


def run_daily_rollover(session: Session, *, now: datetime | None = None) -> int:
    """
    Lodge incomplete tasks from previous days into "today".

    Strategy (simple + demo-friendly):
    - Find tasks with due_at < start_of_today and status != done
    - Mark old task status as rolled_over (keeps history)
    - Create a new task copy due today at 18:00 (local time) with status todo
    """
    now = now or datetime.now()
    start_of_today = datetime.combine(now.date(), time.min)
    default_due_today = datetime.combine(now.date(), time(hour=18, minute=0))
    yesterday_str = (now.date() - timedelta(days=1)).isoformat()

    stmt = (
        select(Task)
        .where(Task.due_at.is_not(None))
        .where(Task.due_at < start_of_today)
        .where(Task.status != TaskStatus.done)
        .where(Task.status != TaskStatus.rolled_over)
    )
    tasks = session.exec(stmt).all()

    created = 0
    for t in tasks:
        t.status = TaskStatus.rolled_over
        t.updated_at = now
        session.add(t)

        new_task = Task(
            title=t.title,
            description=t.description,
            status=TaskStatus.todo,
            due_at=default_due_today,
            original_task_id=t.original_task_id or t.id,
            rolled_over_from_date=t.rolled_over_from_date or yesterday_str,
        )
        session.add(new_task)
        created += 1

    if created:
        session.commit()
    return created

