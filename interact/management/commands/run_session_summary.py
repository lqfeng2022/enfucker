from django.core.management.base import BaseCommand
from interact.models import ChatSession
from interact.usecases.session_summary import session_summary


class Command(BaseCommand):
    help = "Generate a session-wide summary for ChatSession(s)"

    def add_arguments(self, parser):
        parser.add_argument('--session_id', type=int,
                            help='Specific ChatSession ID to summarize')
        parser.add_argument('--all', action='store_true',
                            help='Generate summaries for all sessions with events')

    def handle(self, *args, **options):
        if options['all']:
            session_ids = ChatSession.objects.filter(
                events__isnull=False).distinct().values_list('id', flat=True)
            self.stdout.write(f"Found {len(session_ids)} sessions with events")
        elif options['session_id']:
            session_ids = [options['session_id']]
        else:
            self.stdout.write(self.style.ERROR(
                "Provide --session_id or --all"))
            return

        for session_id in session_ids:
            try:
                session = ChatSession.objects.get(id=session_id)
                summary = session_summary(session=session)
                if summary:
                    self.stdout.write(self.style.SUCCESS(
                        f"Summary generated for session {session_id}"))
                    self.stdout.write("Content:")
                    self.stdout.write(summary.content)
                    self.stdout.write("\nTopics:")
                    self.stdout.write(", ".join(summary.topics))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"No summary generated for session {session_id}"))
            except ChatSession.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"ChatSession {session_id} not found"))
