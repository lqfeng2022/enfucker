from django.core.management.base import BaseCommand
from interact.models import ChatMessage


class Command(BaseCommand):
    help = "Backfill ChatMessage.type based on is_voice and call_session"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting ChatMessage.type backfill...")

        # Call messages (highest priority)
        call_updated = ChatMessage.objects.filter(
            call_session__isnull=False
        ).update(type='call')

        # Audio messages (only those NOT in call)
        audio_updated = ChatMessage.objects.filter(
            call_session__isnull=True,
            is_voice=True
        ).update(type='audio')

        # Text messages (remaining)
        text_updated = ChatMessage.objects.filter(
            call_session__isnull=True,
            is_voice=False
        ).update(type='text')

        # Summary output
        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill completed:\n"
                f"  call: {call_updated}\n"
                f"  audio: {audio_updated}\n"
                f"  text: {text_updated}"
            )
        )