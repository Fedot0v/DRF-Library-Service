from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer
)
from borrowings.telegram_helper import send_telegram_message
from payments.models import Payment
from payments.stripe_helper import create_stripe_session


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)

        message = (
            f"<b>New borrowing</b>\n"
            f"<b>Book:</b> {borrowing.book.title}\n"
            f"<b>User:</b> {borrowing.user.email}\n"
            f"<b>Date of borrowing:</b> {borrowing.date_borrowed}\n"
            f"<b>Expected return date:</b> {borrowing.expected_return_date}\n"
        )

        send_telegram_message(message)

    def get_queryset(self):
        queryset = self.queryset

        if not self.request.user.is_superuser:
            queryset.filter(user=self.request.user)

        is_active = self.request.query_params.get("is_active", None)
        user_id = self.request.query_params.get("user_id", None)

        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=True)

        if self.request.user.is_superuser and user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingSerializer

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        try:
            borrowing = self.get_object()
            if borrowing.actual_return_date is not None:
                return Response(
                    {"detail": "This book has already been returned."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            actual_return_date = timezone.now()
            borrowing.actual_return_date = actual_return_date



            if actual_return_date > borrowing.expected_return_date:
                daily_fee = borrowing.book.daily_fee
                fine_amount = Payment().calculate_fine(
                    expected_return_date=borrowing.expected_return_date,
                    actual_return_date=actual_return_date,
                    daily_fee=daily_fee
                )

                session_url, session_id = create_stripe_session(fine_amount)

                fine_payment = Payment.objects.create(
                    status=Payment.StatusChoices.PENDING,
                    type=Payment.TypeChoices.FINE,
                    money_to_pay=fine_amount,
                    session_url=session_url,
                    session_id=session_id
                )

            borrowing.actual_return_date = timezone.now()
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()

            message = (
                f"<b>Book has been returned</b>\n"
                f"<b>Book:</b> {borrowing.book.title}\n"
                f"<b>User:</b> {borrowing.user.email}\n"
                f"<b>Return Date:</b> {borrowing.actual_return_date}\n"
            )

            send_telegram_message(message)

            return Response(
                BorrowingSerializer(borrowing).data,
                status=status.HTTP_200_OK
            )
        except Borrowing.DoesNotExist:
            return Response(
                {"detail": "This book does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
