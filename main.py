from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sqlmodel import Session

from app.database import engine, init_db
from app.routes.tasks import router as tasks_router
from app.routes.web import router as web_router
from app.services.reminder_service import run_reminder_tick
from app.services.rollover_service import run_daily_rollover

app = FastAPI(title="Task Master", version="0.1.0")

app.include_router(web_router)
app.include_router(tasks_router)

scheduler = BackgroundScheduler()


def _reminder_job():
    with Session(engine) as session:
        run_reminder_tick(session)


def _rollover_job():
    with Session(engine) as session:
        run_daily_rollover(session)


@app.on_event("startup")
def on_startup():
    init_db()

    # reminders every minute (continuous)
    scheduler.add_job(_reminder_job, "interval", minutes=1, id="reminders", replace_existing=True)

    # rollover every day shortly after midnight
    scheduler.add_job(_rollover_job, "cron", hour=0, minute=5, id="rollover", replace_existing=True)

    scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)

