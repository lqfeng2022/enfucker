from django.contrib import admin
from .mixins.admin import HostCountMixin
from .models import (
    BasePrompt, PersonaPrompt, AICompany, HostProfile, AIModel, ModelProvider,
    Voice, Character)


@admin.register(AICompany)
class AICompnayAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

    def formatted_updated_at(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    formatted_updated_at.short_description = 'Updated At'


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'company', 'name', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    search_fields = ['name']

    def formatted_updated_at(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    formatted_updated_at.short_description = 'Updated At'


@admin.register(ModelProvider)
class ModelProviderAdmin(admin.ModelAdmin):
    list_display = ['id', 'usecase', 'step', 'model', 'unit_price', 'unit_amount',
                    'currency', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['usecase', 'step', 'updated_at']

    search_fields = ['model__name']

    def formatted_updated_at(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    formatted_updated_at.short_description = 'Updated At'


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'formatted_created_at']
    list_per_page = 15
    list_filter = ['created_at']

    prepopulated_fields = {'slug': ['name']}

    def formatted_created_at(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    formatted_created_at.short_description = 'Created At'


@admin.register(Voice)
class VoiceAdmin(HostCountMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'character', 'first_language', 'feature',
                    'model', 'host_count', 'formatted_created_at']
    list_per_page = 12
    list_filter = ['first_language', 'character', 'created_at']

    related_field = 'voice_id'
    autocomplete_fields = ['model']
    prepopulated_fields = {'slug': ['name']}

    def formatted_created_at(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    formatted_created_at.short_description = 'Created At'


@admin.register(BasePrompt)
class BasePromptAdmin(HostCountMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'version', 'is_active', 'host_count',
                    'formatted_created_at', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['created_at']

    related_field = 'baseprompt_id'
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

    def formatted_created_at(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    formatted_created_at.short_description = 'Created At'

    def formatted_updated_at(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    formatted_updated_at.short_description = 'Updated At'


@admin.register(PersonaPrompt)
class PersonaPromptAdmin(HostCountMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'role', 'is_active', 'host_count',
                    'formatted_created_at', 'formatted_updated_at']
    list_per_page = 15
    list_filter = ['created_at']

    related_field = 'personaprompt_id'
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

    def formatted_created_at(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    formatted_created_at.short_description = 'Created At'

    def formatted_updated_at(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    formatted_updated_at.short_description = 'Updated At'


@admin.register(HostProfile)
class HostProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'host__name', 'base_prompt', 'persona_prompt', 'voice',
                    'formatted_updated_at']
    list_per_page = 15
    list_filter = ['created_at', 'base_prompt']

    search_fields = ['host__name']

    def formatted_updated_at(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    formatted_updated_at.short_description = 'Updated At'
