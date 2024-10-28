from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookListSerializer

BOOK_URL = reverse("books:book-list")

def sample_book(**params):
    defaults = {
        "title": "Test",
        "author": "<NAME>",
        "cover": "Hard",
        "inventory": 2,
        "daily_fee": 0.3
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class UnauthenticatedUserTest(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.book = sample_book()

    def test_unauthenticated_book_list(self):
        response = self.client.get(BOOK_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthenticatedUserTest(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@mail.com",
            password="<PASSWORD>",
        )
        self.api_client.force_authenticate(user=self.user)

        self.book1 = sample_book(title="Test Book One", author="Test Author", cover="Hard", inventory=2, daily_fee=0.3)
        self.book2 = sample_book(title="Test Book Two", author="Another Author", cover="Soft", inventory=3, daily_fee=0.5)
        self.book3 = sample_book(title="Book Three", author="Test Author", cover="Hard", inventory=1, daily_fee=0.4)

    def test_filter_books_by_title(self):
        res = self.api_client.get(reverse("books:book-list"), {"title": "One"})
        books = Book.objects.filter(title__icontains="One")
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_books_by_author(self):
        res = self.api_client.get(reverse("books:book-list"), {"author": "Test Author"})
        books = Book.objects.filter(author__icontains="Test Author")
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_books_by_cover(self):
        res = self.api_client.get(reverse("books:book-list"), {"cover": "Hard"})
        books = Book.objects.filter(cover__icontains="Hard")
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_books_by_multiple_params(self):
        res = self.api_client.get(reverse("books:book-list"), {"title": "Book", "author": "Test Author"})
        books = Book.objects.filter(title__icontains="Book", author__icontains="Test Author")
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
