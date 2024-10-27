from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from payments.models import Payment
from payments.serializers import PaymentSerializer, PaymentListSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        summary="Create a new payment",
        description="Creates a new payment for the authenticated user.",
        responses={201: PaymentSerializer},
    )
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

    @extend_schema(
        summary="Mark payment as successful",
        description="Marks the payment as successfully processed."
                    " Changes the status to 'PAID'.",
        responses={200: OpenApiResponse(
            description="Payment was successfully processed."
        )}
    )
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

    @extend_schema(
        summary="Cancel a payment",
        description="Indicates that the payment was canceled.",
        responses={200: OpenApiResponse(description="Payment was canceled.")}
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
