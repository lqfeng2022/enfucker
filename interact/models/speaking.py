from django.conf import settings
from django.db import models
from interact.utils.mediauploadto import speaking_audio_upload_to


# interact_speakingsession
class SpeakingSession(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='speaking_sessions')
    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='speaking_sessions')

    def __str__(self) -> str:
        return f"Speaking Attempt - {self.id}"

    class Meta:
        unique_together = ('user', 'product')
        verbose_name_plural = 'Speaking Attempts'


# interact_speakingresponse
class SpeakingResponse(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    session = models.ForeignKey(SpeakingSession, on_delete=models.CASCADE,
                                related_name='responses')

    attempt_number = models.PositiveIntegerField()

    audio = models.FileField(upload_to=speaking_audio_upload_to, null=True,
                             blank=True)
    audio_seconds = models.IntegerField(blank=True, default=0)

    transcript = models.TextField(blank=True)  # stt

    def __str__(self) -> str:
        return f'Response {self.attempt_number} (Session {self.session_id})'

    class Meta:
        unique_together = ('session', 'attempt_number')
        verbose_name_plural = 'Speaking Responses'
        ordering = ['attempt_number']


# interact_speakingevaluation
class SpeakingEvaluation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    response = models.OneToOneField(SpeakingResponse, on_delete=models.CASCADE,
                                    related_name='evaluation')

    fluency_score = models.FloatField(null=True, blank=True)
    lexical_score = models.FloatField(null=True, blank=True)
    grammar_score = models.FloatField(null=True, blank=True)
    pronunciation_score = models.FloatField(null=True, blank=True)

    overall_score = models.FloatField(null=True, blank=True)

    feedback = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'Speaking Evaluation - {self.id}'

    class Meta:
        verbose_name_plural = 'Speaking Evaluation'
        ordering = ['-created_at']


# interact_speakingrewrie
class SpeakingRewrite(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    response = models.ForeignKey(SpeakingResponse, on_delete=models.CASCADE,
                                 related_name='rewrites')

    improved_text = models.TextField()
    band_target = models.DecimalField(max_digits=2, decimal_places=1)

    def __str__(self) -> str:
        return f'Speaking Improvement - {self.id}'

    class Meta:
        unique_together = ('response', 'band_target')
        verbose_name_plural = 'Speaking Improvements'
        ordering = ['band_target']
