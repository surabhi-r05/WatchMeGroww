from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import User
from app.services.alerts import evaluate_user_alerts
from app.core.config import settings
_scheduler=None

def _job_run_all():
    db=SessionLocal()
    try:
        for u in db.scalars(select(User)).all():evaluate_user_alerts(db,u.id)
    finally:db.close()

def start_scheduler():
    global _scheduler
    if _scheduler:return _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except Exception:
        print("[scheduler] APScheduler unavailable")
        return None
    _scheduler=BackgroundScheduler();_scheduler.add_job(_job_run_all,"interval",seconds=settings.alert_interval_seconds,id="alerts",replace_existing=True);_scheduler.start();return _scheduler
