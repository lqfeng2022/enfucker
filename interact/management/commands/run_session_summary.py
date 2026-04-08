from django.core.management.base import BaseCommand
from interact.models import ChatSession
from interact.usecases.session_summary import session_summary


class Command(BaseCommand):
    help = "Generate a session-wide summary for a given ChatSession ID"

    def add_arguments(self, parser):
        parser.add_argument('--session_id', type=int,
                            help='ChatSession ID to summarize')

    def handle(self, *args, **options):
        session_id = options['session_id']
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"ChatSession {session_id} not found"))
            return

        summary = session_summary(session=session)
        if summary:
            self.stdout.write(self.style.SUCCESS(
                f"Session summary generated for session {session_id}")
            )
            self.stdout.write("Content:")
            self.stdout.write(summary.content)
            self.stdout.write("\nTopics:")
            self.stdout.write(", ".join(summary.topics))
        else:
            self.stdout.write(self.style.WARNING(
                f"No summary generated for session {session_id}"))
