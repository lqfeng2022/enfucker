from rest_framework import serializers
from django.utils import timezone
from .models import CreditVoucher, CreditAccount


class CreditCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditAccount
        fields = ['id', 'balance', 'lifetime_credits', 'lifetime_debits',
                  'updated_at']


class CreditVoucherListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditVoucher
        fields = ['id', 'code', 'credits', 'redeemed_at', 'redeemed',
                  'expires_at']


class CreditVoucherRedeemSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=32)

    def validate_code(self, value):
        try:
            voucher = CreditVoucher.objects.get(code=value)
        except CreditVoucher.DoesNotExist:
            raise serializers.ValidationError("Voucher not found.")

        if voucher.redeemed:
            raise serializers.ValidationError("Voucher already redeemed.")

        if voucher.expires_at and voucher.expires_at < timezone.now():
            raise serializers.ValidationError("Voucher has expired.")

        # Pass the voucher instance to the view
        self.context['voucher'] = voucher
        return value
