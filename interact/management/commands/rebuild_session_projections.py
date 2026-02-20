from django.core.management.base import BaseCommand
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from interact.models import (
    ChatSession, ChatMessage, ModelUsage, DebitLedger, CallSession,
)


class Command(BaseCommand):
    help = "Rebuild ChatSession projection fields (cost, credits, audio durations)"

    def handle(self, *args, **options):
        self.stdout.write("Rebuilding ChatSession projections...")

        sessions = ChatSession.objects.all()

        for session in sessions.iterator():
            # 🔹 Cost projection (DecimalField)
            cost = ModelUsage.objects.filter(session=session).aggregate(
                total=Coalesce(Sum('cost'), Value(0),
                               output_field=DecimalField())
            )['total']

            # 🔹 Credits projection (IntegerField)
            credits = DebitLedger.objects.filter(usage__session=session). \
                aggregate(total=Coalesce(Sum('amount'), Value(0)))['total']

            # 🔹 User audio
            user_audio = ChatMessage.objects.filter(
                session=session, role=ChatMessage.USER, is_voice=True). \
                aggregate(total=Coalesce(Sum('audio_seconds'),
                                         Value(0)))['total']

            # 🔹 Assistant audio (IntegerField)
            assistant_audio = ChatMessage.objects.filter(
                session=session, role=ChatMessage.ASSISTANT, is_voice=True,). \
                aggregate(total=Coalesce(Sum('audio_seconds'), Value(0))
                          )['total']

            # 🔹 Call audio (IntegerField)
            call_audio = CallSession.objects.filter(session=session). \
                aggregate(total=Coalesce(Sum('duration_seconds'), Value(0))
                          )['total']

            # 🔹 Atomic update
            ChatSession.objects.filter(id=session.id).update(
                cost=cost,
                credits_used=credits,
                user_audio_seconds=user_audio,
                assistant_audio_seconds=assistant_audio,
                call_audio_seconds=call_audio,
            )

            self.stdout.write(
                self.style.SUCCESS("Projection rebuild complete.")
            )
