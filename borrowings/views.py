from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
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

    @extend_schema(
        summary="Create new borrowing",
        description="Creates a new borrowing record for the currently"
                    " authorized user and sends a message to Telegram.",
        responses={201: BorrowingSerializer}
    )
    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)

        message = (
            f"<b>New borrowing</b>\n"
            f"<b>Book:</b> {borrowing.book.title}\n"
            f"<b>User:</b> {borrowing.user.email}\n"
            f"<b>Date of borrowing:</b> {borrowing.borrow_date}\n"
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

    @extend_schema(
        summary="Return book",
        description="Marks the book as returned. If returned late, a penalty"
                    " payment is generated through Stripe.",
        responses={
            200: OpenApiResponse(
                response=BorrowingSerializer,
                description="Info about borrowing"
            ),
            400: OpenApiResponse(
                description="Book already returned or doesn't exist"
            )
        },
    )
    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        try:
            borrowing = self.get_object()
            if borrowing.actual_return_date is not None:
                return Response(
                    {"detail": "This book has already been returned."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            actual_return_date = timezone.now().date()
            borrowing.actual_return_date = actual_return_date

            session_url, session_id = create_stripe_session(borrowing, request)

            borrowing.save()

            message = (
                f"<b>Book has been returned</b>\n"
                f"<b>Book:</b> {borrowing.book.title}\n"
                f"<b>User:</b> {borrowing.user.email}\n"
                f"<b>Return Date:</b> {borrowing.actual_return_date}\n"
            )

            send_telegram_message(message)

            return Response(
                {"session_url": session_url},
                status=status.HTTP_200_OK
            )
        except Borrowing.DoesNotExist:
            return Response(
                {"detail": "This book does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
    @extend_schema(
        summary="Get list of borrowings",
        description="Returns a list of borrowings. For ordinary users - only"
                    " their borrowings."
                    "For superusers - you can filter by the `is_active` and "
                    "`user_id` parameters.",
        parameters=[
            OpenApiParameter(
                "is_active",
                bool,
                description=(
                        "Filter by activity status (true or false)"
                ),

            ),
            OpenApiParameter("user_id", int, description=(
                    "Filter by user ID (superusers only)"
            ))
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)