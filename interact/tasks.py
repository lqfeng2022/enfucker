# interact/tasks.py
from celery import shared_task, chain
from interact.usecases.event_summary import session_event_summary
from interact.usecases.session_summary import session_summary
from interact.services.session_filters import get_sessions_for_event_summary
from interact.models import ChatSession
import logging

logger = logging.getLogger(__name__)


# Daily task with celery beat
@shared_task()
def summarize_session_events_task():
    session_ids = get_sessions_for_event_summary()

    for session_id in session_ids:
        # After events are generated, update session summary
        chain(
            session_event_summary_task.s(session_id),
            update_session_summary_task.si(session_id)
        ).apply_async()


# Per-session event generation
@shared_task()
def session_event_summary_task(session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
        session_event_summary(session=session)
    except ChatSession.DoesNotExist:
        logger.warning(f"Session {session_id} not found")
    except Exception:
        logger.exception(f"Failed event summary for session {session_id}")
        raise  # let Celery retry if needed


# Update(generate) session summary task
@shared_task()
def update_session_summary_task(session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
    except ChatSession.DoesNotExist:
        logger.warning(f"Session {session_id} not found")
        return

    summary = session_summary(session=session)
    if summary:
        logger.info(f"Updated session {session_id}")


# NOTE:
# 1. @shared_task() KEYWROD ARGUMENTS:
# bind=True: Gives you access to self (the task instance).
# autoretry_for: Automatically retries when one of these exceptions is raised.
# retry_kwargs: Controls how many times Celery retries.
# retry_backoff: Adds exponential backoff (10s > 20s > 40s)

# 2. chain() - DEPENDENT WORKFLOW
# chain() make sure the executing order
# .s() creates a signature — lightweight object for chaining tasks.
# .si() prevents Celery from injecting the previous task result
# apply_async() schedules the chain on the broker immediately.
