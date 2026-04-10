from django.core.management.base import BaseCommand
from interact.models import ChatSession
from interact.usecases.event_summary import session_event_summary


class Command(BaseCommand):
    help = "Run session event summary for specific session"

    def add_arguments(self, parser):
        parser.add_argument('--session_id', type=int)

    def handle(self, *args, **options):
        session_id = options.get('session_id')

        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            self.stdout.write(self.style.ERROR("Session not found"))
            return

        session_event_summary(session=session)
