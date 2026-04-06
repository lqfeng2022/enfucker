from django.core.management.base import BaseCommand
from interact.models import ChatSession
from interact.usecases.summary_event import session_event_summary
from datetime import datetime


class Command(BaseCommand):
    help = "Run session event summary for specific session"

    def add_arguments(self, parser):
        parser.add_argument('--session_id', type=int)
        parser.add_argument('--target_date', type=str, help='Date to summarize (YYYY-MM-DD)')

    def handle(self, *args, **options):
        session_id = options.get('session_id')
        target_date_str = options.get('target_date')

        # Parse target_date if provided
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(f"Invalid date format: {target_date_str}. Use YYYY-MM-DD")
                return

        if session_id:
            sessions = ChatSession.objects.filter(id=session_id)
        else:
            sessions = ChatSession.objects.all()

        for session in sessions:
            session_event_summary(session=session, target_date=target_date)
