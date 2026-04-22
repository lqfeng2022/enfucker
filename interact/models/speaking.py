from django.conf import settings
from django.db import models
from interact.utils.mediauploadto import speaking_audio_upload_to


# interact_mocktest
class MockTest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    title = models.CharField(max_length=255)

    playlist = models.OneToOneField(settings.STORE_PLAYLIST_MODEL, on_delete=models.CASCADE,
                                    related_name='mock_test')

    def __str__(self) -> str:
        return f"{self.title}"

    class Meta:
        verbose_name_plural = 'Mock Tests'


# interact_speakingattempt
class SpeakingAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='attempts')
    mock_test = models.ForeignKey(MockTest, on_delete=models.CASCADE,
                                  related_name='attempts')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='in_progress')

    overall_score = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Speaking Attempt - {self.id}"

    class Meta:
        verbose_name_plural = 'Speaking Attempts'
        ordering = ['-started_at']


# interact_speakinganswer
class SpeakingAnswer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)

    order = models.PositiveIntegerField()

    audio = models.FileField(upload_to=speaking_audio_upload_to)
    audio_seconds = models.IntegerField(blank=True)
    transcript = models.TextField(blank=True)  # stt
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='pending')

    product = models.ForeignKey(settings.STORE_PRODUCT_MODEL, on_delete=models.CASCADE,
                                related_name='speaking_answers')
    attempt = models.ForeignKey(SpeakingAttempt, on_delete=models.CASCADE,
                                related_name='answers')

    def __str__(self) -> str:
        return f'Speaking Answer - {self.id}'

    class Meta:
        unique_together = ('product', 'attempt')
        indexes = [
            models.Index(fields=['attempt', 'order']),
        ]
        verbose_name_plural = 'Speaking Answers'
        ordering = ['order']


# interact_speakingevaluation
class SpeakingEvaluation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    answer = models.OneToOneField(SpeakingAnswer, on_delete=models.CASCADE,
                                  related_name='evaluation')

    scores = models.JSONField(default=dict)
    overall_score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'Speaking Evaluation - {self.id}'

    class Meta:
        verbose_name_plural = 'Speaking Evaluation'
        ordering = ['-created_at']


# interact_speakingrewrite
class SpeakingRewrite(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    answer = models.OneToOneField(SpeakingAnswer, on_delete=models.CASCADE,
                                  related_name='rewrite')

    content = models.TextField()

    def __str__(self) -> str:
        return f'Speaking Rewrite - {self.id}'

    class Meta:
        verbose_name_plural = 'Speaking Rewrites'
