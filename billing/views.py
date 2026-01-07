from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from .serializers import (
    CreditVoucherRedeemSerializer, CreditVoucherListSerializer, CreditCountSerializer
)
from .services.voucher import redeem_voucher
from .models import CreditVoucher, CreditAccount


class CreditViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAdminUser]

    serializer_class = CreditCountSerializer
    queryset = CreditAccount.objects.all()

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def me(self, request):
        credit = CreditAccount.objects.get(user=request.user)
        serializer = CreditCountSerializer(credit)
        return Response(serializer.data)


class VoucherViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CreditVoucherListSerializer
        return CreditVoucherRedeemSerializer

    def get_queryset(self):
        user = self.request.user
        return CreditVoucher.objects.filter(redeemed_by=user)

    @action(detail=False, methods=['post'], url_path='redeem')
    def redeem(self, request):
        serializer = CreditVoucherRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        voucher = serializer.context['voucher']  # get the voucher instance
        user = request.user

        try:
            result = redeem_voucher(voucher=voucher, user=user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Voucher redeemed successfully", **result},
            status=status.HTTP_200_OK
        )
