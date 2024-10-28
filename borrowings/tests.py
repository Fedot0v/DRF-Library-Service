from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer
from payments.models import Payment

BORROWING_URL = reverse("borrowings:borrowing-list")


def sample_borrowing(user, book, **params):
    defaults = {
        "expected_return_date": "2024-10-29",
        "book": book.id,
        "user": user.id
    }
    defaults.update(params)
    return defaults


class UnauthenticatedBorrowingTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingTest(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@mail.com",
            password="<PASSWORD>",
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Hard",
            inventory=2,
            daily_fee=0.3
        )
        self.api_client.force_authenticate(user=self.user)

    def test_borrowing_list(self):
        res = self.api_client.get(BORROWING_URL)

        borrowings = Borrowing.objects.all()
        serializer = BorrowingListSerializer(borrowings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_borrowing_list(self):
        borrowing_payload = sample_borrowing(user=self.user, book=self.book)
        self.api_client.post(BORROWING_URL, borrowing_payload)

        res = self.api_client.get(BORROWING_URL, {"is_active": "true"})
        borrowings = Borrowing.objects.filter(actual_return_date__isnull=True)
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_borrowing(self):
        borrowing_url = reverse("borrowings:borrowing-list")
        payload = sample_borrowing(user=self.user, book=self.book)

        res = self.api_client.post(borrowing_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.filter(
            book=self.book,
            user=self.user
        ).first()
        self.assertIsNotNone(
            borrowing,
            "Borrowing should have been created."
        )

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)

    def test_return_book(self):
        borrowing_payload = sample_borrowing(user=self.user, book=self.book)
        create_res = self.api_client.post(
            reverse("borrowings:borrowing-list"),
            borrowing_payload,
            )

        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.filter(
            user=self.user,
            book=self.book
        ).first()
        self.assertIsNotNone(
            borrowing,
            "Borrowing should exist for the user and book."
        )

        return_url = reverse(
            "borrowings:return-book",
            kwargs={"pk": borrowing.pk}
        )

        res = self.api_client.post(return_url)

        borrowing.refresh_from_db()
        self.book.refresh_from_db()


        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(borrowing.actual_return_date)

        self.assertEqual(self.book.inventory, 2)

    @patch("borrowings.views.create_stripe_session")
    def test_return_book_with_stripe_called(self, mock_create_stripe_session):
        borrowing_payload = sample_borrowing(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timedelta(days=1))

        create_res = self.api_client.post(
            reverse("borrowings:borrowing-list"),
            borrowing_payload
        )

        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.filter(
            user=self.user,
            book=self.book
        ).first()
        self.assertIsNotNone(
            borrowing,
            "Borrowing should exist for the user and book."
        )

        return_url = reverse(
            "borrowings:return-book",
            kwargs={"pk": borrowing.pk}
        )

        mock_create_stripe_session.return_value = (
            "session_url",
            "session_id"
        )

        res = self.api_client.post(return_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertTrue(mock_create_stripe_session.called)

        borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertIsNotNone(borrowing.actual_return_date)

        self.assertEqual(self.book.inventory, 2)

class AdminBorrowingTest(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="test@mail.com",
            password="<PASSWORD>",
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Hard",
            inventory=2,
            daily_fee=0.3
        )
        self.api_client.force_authenticate(user=self.user)

    def test_admin_borrowing_list_filter(self):
        borrowing_payload = sample_borrowing(user=self.user, book=self.book)
        self.api_client.post(BORROWING_URL, borrowing_payload)

        res_is_active = self.api_client.get(BORROWING_URL, {"is_active": "true"})
        res_user_id = self.api_client.get(BORROWING_URL, {"user_id": 1})

        borrowings1 = Borrowing.objects.filter(actual_return_date__isnull=True)
        serializer1 = BorrowingListSerializer(borrowings1, many=True)

        borrowings2 = Borrowing.objects.filter(user_id=1)
        serializer2 = BorrowingListSerializer(borrowings2, many=True)

        self.assertEqual(res_is_active.status_code, status.HTTP_200_OK)
        self.assertEqual(res_is_active.data, serializer1.data)

        self.assertEqual(res_user_id.status_code, status.HTTP_200_OK)
        self.assertEqual(res_user_id.data, serializer2.data)
