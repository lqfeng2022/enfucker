import uuid
from django.conf import settings
from datetime import timedelta
from django.db import models
from django.utils import timezone


# billing_payment -> money in
class Payment(models.Model):
    ALIPAY = 'alipay'
    PAYPAL = 'paypal'
    STRIPE = 'stripe'
    PROVIDER_CHOICES = [(ALIPAY, 'Alipay'), (PAYPAL, 'PayPal'),
                        (STRIPE, 'Stripe')]

    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    STATUS_CHOICES = [(PENDING, 'Pending'), (PAID, 'Paid'), (FAILED, 'Failed'),
                      (REFUNDED, 'Refunded')]

    # user fk
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='payments')

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_trade_id = models.CharField(max_length=128, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default=PENDING)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.amount}{self.currency} - {self.provider}'

    class Meta:
        indexes = [models.Index(fields=['provider', 'provider_trade_id'])]


# billing.creditaccount -> account balance
class CreditAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='credit_account')

    balance = models.PositiveIntegerField(default=0)
    lifetime_credits = models.PositiveIntegerField(default=0)
    lifetime_debits = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user_id}: {self.balance} credits'

    class Meta:
        verbose_name_plural = 'Credit Accounts'
        ordering = ['updated_at']


# billing.creditvoucher -> money/credits
class CreditVoucher(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)

    PACKAGE_CHOICES = [(1000, '1,000 credits'), (5000, '5,000 credits'),
                       (10000, '10,000 credits'), (50000, '50,000 credits'),
                       (100000, '100,000 credits'), (500000, '500,000 credits'),
                       (1000000, '1,000,000 credits')]

    credits = models.PositiveIntegerField(choices=PACKAGE_CHOICES)
    code = models.CharField(max_length=32, unique=True, editable=False)

    # user pk
    redeemed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    redeemed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex.upper()[:12]
        # Auto-set expiry ONLY on creation
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=365)
        self.is_expired = timezone.now() >= self.expires_at
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.credits} credits'

    class Meta:
        verbose_name_plural = 'Credit Vouchers'
        ordering = ['created_at']
