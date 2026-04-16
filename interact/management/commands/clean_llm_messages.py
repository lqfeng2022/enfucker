import re
from django.core.management.base import BaseCommand
from django.db import transaction
from interact.models import ChatMessage


BATCH_SIZE = 500


def format_message_text(text: str) -> str:
    if not text:
        return ''

    # Normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove parenthesized content (iterative)
    while True:
        cleaned = re.sub(r'\([^()]*\)', '', text)
        if cleaned == text:
            break
        text = cleaned

    text = text.replace('*', '')  # Remove all asterisks
    text = re.sub(r'\s*—\s*', ' ', text)  # Use space instead of em-dash
    text = text.replace('\n', ' ')  # Convert newlines to space (chat style)
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces

    return text.strip()


class Command(BaseCommand):
    help = "Format assistant messages"

    def handle(self, *args, **options):
        qs = ChatMessage.objects. \
            filter(role=ChatMessage.ASSISTANT). \
            only("id", "content", "enhanced_content")

        total = qs.count()
        self.stdout.write(f"Processing {total} assistant messages...")

        updated = 0

        for start in range(0, total, BATCH_SIZE):
            batch = list(qs[start:start + BATCH_SIZE])

            to_update = []

            for msg in batch:
                changed = False

                # ---- content ----
                original = msg.content or ""
                formatted = format_message_text(original)

                if original != formatted:
                    msg.content = formatted
                    changed = True

                # ---- enhanced_content ----
                enhanced = msg.enhanced_content or ""

                if enhanced:
                    formatted_enhanced = format_message_text(enhanced)

                    if enhanced != formatted_enhanced:
                        msg.enhanced_content = formatted_enhanced
                        changed = True

                if changed:
                    to_update.append(msg)

            if to_update:
                with transaction.atomic():
                    ChatMessage.objects.bulk_update(
                        to_update,
                        ["content", "enhanced_content"]
                    )

            updated += len(to_update)
            self.stdout.write(f"Updated {updated}/{total}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Updated {updated} messages."
        ))
