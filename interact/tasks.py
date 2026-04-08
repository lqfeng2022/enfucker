# interact/tasks.py
from celery import shared_task
from interact.usecases.summary import maybe_summarize_session
from interact.usecases.event_summary import session_event_summary
from interact.usecases.session_summary import session_summary
from interact.services.session_filters import get_sessions_for_event_summary
from interact.models import ChatSession
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={'max_retries': 3}
)
def summarize_session_task(self, session_id):
    session = ChatSession.objects.get(id=session_id)
    maybe_summarize_session(session=session)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={'max_retries': 3}
)
def summarize_session_events_task(self):
    """
    Run daily: generate events for ALL active sessions
    """
    # print("🔥 CELERY BEAT TEST TRIGGERED")
    session_ids = get_sessions_for_event_summary()

    for session_id in session_ids:
        # --- Step 1: Generate session events ---
        session_event_summary.delay(session_id)

        # --- Step 2: After events are generated, update session summary ---
        # We can fire a follow-up task (delayed), assuming events are created fast
        update_session_summary_task.delay(session_id)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={'max_retries': 2}
)
def update_session_summary_task(self, session_id):
    """
    Generate or update a session-wide summary for a single session.
    """
    try:
        session = ChatSession.objects.get(id=session_id)
    except ChatSession.DoesNotExist:
        logger.warning(f"Session {session_id} not found")
        return

    summary = session_summary(session=session)
    if summary:
        logger.info(f"Session summary updated for session {session_id}")
    else:
        logger.warning(f"Session summary failed for session {session_id}")

# bind=True: Gives you access to self (the task instance).
# autoretry_for: Automatically retries when one of these exceptions is raised.
# retry_kwargs: Controls how many times Celery retries.
# retry_backoff: Adds exponential backoff (10s > 20s > 40s)
