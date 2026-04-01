# memory/models.py
from django.db import models
from django.conf import settings


class AbstractCommon(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# user languages
class UserLanguage(AbstractCommon):
    LANGUAGE_TYPE_CHOICES = [
        ('native', 'Native'),
        ('target', 'Target'),
    ]

    LANGUAGE_LEVEL_CHOICES = [
        ('A1', 'Beginner'),
        ('A2', 'Elementary'),
        ('B1', 'Intermediate'),
        ('B2', 'Upper-Intermediate'),
        ('C1', 'Advanced'),
        ('C2', 'Mastery')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    language = models.ForeignKey(settings.STORE_LANGUAGE_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=LANGUAGE_TYPE_CHOICES, 
                            default='native')
    level = models.CharField(max_length=20, choices=LANGUAGE_LEVEL_CHOICES, 
                             null=True, blank=True)

    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'language', 'type')

    def __str__(self):
        return f"{self.user_id}-{self.language_id}-{self.type}"
    

# global identity
class UserMemory(AbstractCommon):
    OCCUPATION_TYPE_CHOICES = [
        ('study', 'Study'),
        ('work', 'Work'),
    ]
        
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # We really care about:
    occupation = models.CharField(max_length=10, choices=OCCUPATION_TYPE_CHOICES, 
                                  default='study')
    longterm_goal = models.CharField(max_length=255, blank=True)
    current_goal = models.CharField(max_length=255, blank=True)

    # JSON for flexible storage
    # WHO ARE U: goals, interests, identity(job, student), motivation
    profile = models.JSONField(default=dict, blank=True)
    # HOW TO INTERACT: correction style
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"UserMemory<{self.user_id}>"
    

# relationship context
class UserAgentMemory(AbstractCommon):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    host = models.ForeignKey(settings.STORE_HOST_MODEL, on_delete=models.CASCADE)

    relationship_level = models.FloatField(default=0)
    trust_level = models.FloatField(default=0)

    # observed patterns: mistakes
    behavior = models.JSONField(default=dict, blank=True) 
    # how to interact
    preferences = models.JSONField(default=dict, blank=True) 

    first_interaction_at = models.DateTimeField(null=True, blank=True)
    last_interaction_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'host')

    def __str__(self):
        return f"UserAgentMemory<{self.user_id}-{self.host_id}>"
    

# atomic facts/events
class MemoryItem(AbstractCommon):
    MEMORY_TYPE_CHOICES = [
        ('fact', 'Fact'),
        ('mistake', 'Mistake'),
        ('preference', 'Preference'),
        ('event', 'Event'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    host = models.ForeignKey(settings.STORE_HOST_MODEL, on_delete=models.CASCADE,
                             null=True, blank=True)

    type = models.CharField(max_length=20, choices=MEMORY_TYPE_CHOICES, default='fact')
    content = models.TextField()

    importance = models.FloatField(default=0.5)
    confidence = models.FloatField(default=0.8)

    def __str__(self):
        return f"{self.type}: {self.content[:30]}"

    # # Mistake  
    # {
    #   "type": "mistake",
    #   "content": "User հաճախ omits articles like 'a' and 'the'",
    #   "importance": 0.8
    # }

    # # Preference
    # {
    #   "type": "preference",
    #   "content": "User prefers corrections after finishing speaking",
    #   "importance": 0.9
    # }

    # # Fact (stable info)
    # {
    #   "type": "fact",
    #   "content": "User is preparing for English job interviews",
    #   "importance": 0.85
    # }

    # # Event (episodic memory)
    # {
    #   "type": "event",
    #   "content": "User successfully explained a full yoga routine in English",
    #   "importance": 0.7
    # }