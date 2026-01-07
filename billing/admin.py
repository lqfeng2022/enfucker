from django.contrib import admin
from . import models


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'provider', 'provider_trade_id', 'amount',
                    'currency', 'status', 'created_at', 'paid_at']
    list_per_page = 15
    list_filter = ['provider', 'status', 'created_at']

    search_fields = ['user__username']


@admin.register(models.CreditAccount)
class CreditAccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'balance', 'lifetime_credits', 'lifetime_debits',
                    'updated_at']
    list_per_page = 15
    list_filter = ['updated_at']

    search_fields = ['user__username']
    readonly_fields = ['user', 'balance', 'lifetime_credits',
                       'lifetime_debits']


@admin.register(models.CreditVoucher)
class CreditVoucherAdmin(admin.ModelAdmin):
    list_display = ['id', 'credits', 'code', 'redeemed_by', 'redeemed_at',
                    'created_at']
    list_per_page = 15
    list_filter = ['credits', 'created_at']

    search_fields = ['credits']
    readonly_fields = ['code']
