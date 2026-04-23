from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.models import Task, TaskStatus

try:
    from plyer import notification
except Exception:  # pragma: no cover
    notification = None


def _notify(title: str, message: str) -> None:
    if notification is None:
        print(f"[REMINDER] {title} - {message}")
        return
    notification.notify(title=title, message=message, timeout=10)


def run_reminder_tick(
    session: Session,
    *,
    remind_window_minutes: int = 15,
    min_gap_minutes: int = 10,
    now: Optional[datetime] = None,
) -> int:
    """
    Send reminders for tasks due soon.

    - Only reminds tasks not done
    - Only reminds when due_at is within [now, now+window]
    - Rate limits per task using last_reminded_at
    """
    now = now or datetime.now()
    window_end = now + timedelta(minutes=remind_window_minutes)
    min_gap = timedelta(minutes=min_gap_minutes)

    stmt = (
        select(Task)
        .where(Task.due_at.is_not(None))
        .where(Task.status != TaskStatus.done)
        .where(Task.due_at >= now)
        .where(Task.due_at <= window_end)
        .order_by(Task.due_at)
    )
    tasks = session.exec(stmt).all()

    sent = 0
    for t in tasks:
        if t.last_reminded_at and (now - t.last_reminded_at) < min_gap:
            continue

        when = t.due_at.strftime("%Y-%m-%d %H:%M") if t.due_at else "soon"
        _notify("Task reminder", f"{t.title} (due {when})")

        t.last_reminded_at = now
        t.reminder_count = (t.reminder_count or 0) + 1
        t.updated_at = now
        session.add(t)
        sent += 1

    if sent:
        session.commit()
    return sent

