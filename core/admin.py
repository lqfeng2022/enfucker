from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from store.mixins.admin import FormattedUpdateDateMixin
from .models import User, UserLog, Profile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'first_name', 'last_name',
                    'email', 'is_staff', 'is_active', 'date_joined', 'last_login']
    list_per_page = 20

    list_filter = ['is_staff', 'is_superuser', 'is_active']

    add_fieldsets = (
        (None, {
            'classes': ('wide'),
            'fields': (
                'username',
                'usable_password',
                'password1',
                'password2',
                'email',
                'first_name',
                'last_name'
            ),
        }),
    )


@admin.register(UserLog)
class UseragentAdmin(FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'user', 'ip', 'user_agent', 'sessid',
                    'formatted_updated_at']
    list_per_page = 15
    list_filter = ['ip', 'device', 'os', 'browser', 'updated_at']

    search_fields = ['user_agent']

    ordering = ['id']


@admin.register(Profile)
class ProfileAdmin(FormattedUpdateDateMixin, admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'bro', 'city',
                    'formatted_updated_at']
    list_per_page = 15

    # prefetch the related user, avoid N + 1 queries problem
    list_select_related = ['user']
    list_filter = ['bro', 'updated_at', 'created_at']

    search_fields = ['first_name__istartswith', 'last_name__istartswith']
    # 'first_name__istartswith' works, cus user is a one-to-one field
    # i: short for insensitive

    ordering = ['user__first_name', 'user__last_name']

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name
