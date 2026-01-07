from celery import shared_task
from interact.usecases.summary import maybe_summarize_session
from interact.models import ChatSession


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={'max_retries': 3}
)
def summarize_session_task(self, session_id):
    session = ChatSession.objects.get(id=session_id)
    maybe_summarize_session(session=session)


# bind=True: Gives you access to self (the task instance).
# autoretry_for: Automatically retries when one of these exceptions is raised.
# retry_kwargs: Controls how many times Celery retries.
# retry_backoff: Adds exponential backoff (10s > 20s > 40s)
