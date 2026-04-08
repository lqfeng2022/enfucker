# interact/management/commands/backfill_session_events.py
from django.core.management.base import BaseCommand
from datetime import timedelta
from interact.models import ChatSession
from interact.usecases.summary_event import session_event_summary


class Command(BaseCommand):
    help = "Backfill session events for all sessions"

    def handle(self, *args, **options):
        sessions = ChatSession.objects.all()

        for session in sessions:
            self.stdout.write(f"Processing session {session.id}")
            self._process_session(session)

    def _process_session(self, session):
        messages = session.messages.order_by("created_at").only("created_at")

        if not messages.exists():
            return

        # earliest message date (UTC)
        first_msg = messages.first().created_at.date()
        last_msg = messages.last().created_at.date()

        current_date = first_msg

        while current_date <= last_msg:
            try:
                session_event_summary(
                    session=session,
                    target_date=current_date
                )
            except Exception as e:
                self.stderr.write(
                    f"Error session {session.id} date {current_date}: {e}"
                )

            current_date += timedelta(days=1)
