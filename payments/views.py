from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from payments.models import Payment
from payments.serializers import PaymentSerializer, PaymentListSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset.all()
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer

    @action(
        detail=True, methods=["get"],
        url_path="success",
        url_name="payment-success"
    )
    def success(self, request, pk=None):
        payment = self.get_object()
        payment.status = Payment.StatusChoices.PAID
        payment.save()
        return Response(
            {"message": "Payment was successfully processed."},
            status=status.HTTP_200_OK
        )
    @action(
        detail=True,
        methods=["get"],
        url_path="cancel",
        url_name="payment-cancel"
    )
    def cancel(self, request, pk=None):
        return Response(
            {"message": "Payment was canceled."},
            status=status.HTTP_200_OK
        )
