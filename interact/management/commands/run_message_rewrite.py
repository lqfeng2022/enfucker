from django.core.management.base import BaseCommand
from interact.models import ChatMessage
from interact.usecases.rewrite import session_message_rewrite


class Command(BaseCommand):
    help = "Run rewrite task for use message"

    def add_arguments(self, parser):
        parser.add_argument('--message_id', type=int)

    def handle(self, *args, **options):
        message_id = options.get('message_id')

        if not message_id:
            self.stdout.write(self.style.WARNING("No message_id provided"))
            return

        try:
            message = ChatMessage.objects.get(id=message_id)
        except ChatMessage.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"ChatMessage {message_id} not found")
            )
            return

        session_message_rewrite(message=message)
        self.stdout.write(
            self.style.SUCCESS(f"Rewrite completed for message {message_id}")
        )
