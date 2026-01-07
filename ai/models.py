from django.db import models
from django.conf import settings
from ai.contracts import CHAT, STT, TTS, SUMMARY, ENHANCE


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ai_aicompany
class AICompany(AbstractCommon):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = 'AI Companies'
        ordering = ['id']


# ai_aimodel
class AIModel(AbstractCommon):
    name = models.CharField(max_length=255, unique=True)
    company = models.ForeignKey(AICompany, on_delete=models.CASCADE,
                                related_name='aimodels')

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = ('company', 'name')
        verbose_name_plural = 'AI Models'
        ordering = ['id']


# ai_modelprovider
class ModelProvider(AbstractCommon):
    USECASE_CHOICES = [(STT, 'STT'), (TTS, 'TTS'), (CHAT, 'LLM-Chat'),
                       (SUMMARY, 'LLM-Summary'), (ENHANCE, 'LLM-Enhance'),]

    TOKENS = 'tokens'
    CHARACTERS = 'characters'
    SECONDS = 'seconds'
    AMOUNT_CHOICES = [(TOKENS, '1K Tokens'), (CHARACTERS, '1 Character'),
                      (SECONDS, '1 Second')]

    INPUT, CACHED_INPUT, OUTPUT = 'input', 'cached-input', 'output'
    STEP_CHOICES = [(INPUT, 'Input'), (CACHED_INPUT, 'Cached Input'),
                    (OUTPUT, 'Output')]

    model = models.ForeignKey(AIModel, on_delete=models.CASCADE,
                              related_name='modelproviders')
    usecase = models.CharField(max_length=32, choices=USECASE_CHOICES,
                               default=CHAT)
    step = models.CharField(max_length=255, choices=STEP_CHOICES,
                            default=INPUT)

    unit_price = models.DecimalField(max_digits=12, decimal_places=6,
                                     default=0)
    unit_amount = models.CharField(max_length=32, choices=AMOUNT_CHOICES)
    currency = models.CharField(max_length=3, default='USD')

    def __str__(self) -> str:
        return f'{self.model}'

    class Meta:
        unique_together = ('model', 'usecase', 'step')
        verbose_name_plural = 'Model Providers'
        ordering = ['id']


# ai_character
class Character(AbstractCommon):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = 'AI Characters'
        ordering = ['id']


# ai_voice
class Voice(AbstractCommon):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField()

    character = models.ForeignKey(Character, on_delete=models.PROTECT)
    feature = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    model = models.ForeignKey(ModelProvider, on_delete=models.CASCADE,
                              related_name='voices')
    voice_id = models.CharField(max_length=255, unique=True)

    first_language = models.ForeignKey(settings.STORE_LANGUAGE_MODEL,
                                       on_delete=models.PROTECT, related_name='voices')

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} - {self.feature}'

    class Meta:
        verbose_name_plural = 'Model Voices'
        ordering = ['created_at']


# ai_baseprompt
class BasePrompt(AbstractCommon):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField()

    content = models.TextField(blank=True)

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.name}'

    class Meta:
        verbose_name_plural = 'Base Prompts'
        ordering = ['created_at']


# ai_personaprompt
class PersonaPrompt(AbstractCommon):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField()
    role = models.CharField(max_length=255)  # English teacher, doctor, etc.

    identity = models.TextField(blank=True)  # Situational awareness
    personality = models.TextField(blank=True)  # Personality (with a flaw)
    communication_style = models.TextField(blank=True)  # Communication style
    behavior = models.TextField(blank=True)  # Persona-specific, not global
    constraints = models.TextField(blank=True)  # Non-negotiable

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.name} - {self.role}'

    class Meta:
        verbose_name_plural = 'Persona Prompts'
        ordering = ['created_at']


# ai_hostprofile
class HostProfile(AbstractCommon):
    host = models.OneToOneField(settings.STORE_HOST_MODEL, on_delete=models.CASCADE,
                                related_name='host_profile')

    cover = models.ImageField(upload_to='ai/image/host-back', null=True)
    portrait = models.ImageField(upload_to='ai/image/host-avatar',
                                 null=True)

    base_prompt = models.ForeignKey(BasePrompt, on_delete=models.PROTECT,
                                    related_name='host_profiles')
    persona_prompt = models.ForeignKey(PersonaPrompt, on_delete=models.PROTECT,
                                       related_name='host_profiles')

    chat_model = models.ForeignKey(AIModel, on_delete=models.PROTECT,
                                   related_name='chat_hosts')
    stt_model = models.ForeignKey(AIModel, on_delete=models.PROTECT,
                                  related_name='stt_hosts')
    tts_model = models.ForeignKey(AIModel, on_delete=models.PROTECT,
                                  related_name='tts_hosts')

    voice = models.ForeignKey(Voice, on_delete=models.PROTECT,
                              related_name='host_profiles')

    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.host}'

    class Meta:
        verbose_name_plural = 'Host Profiles'
        ordering = ['created_at']
