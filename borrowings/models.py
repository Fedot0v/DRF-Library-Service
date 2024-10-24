from django.db import models

from books.models import Book
from library_service import settings


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField()
    book_id = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name="borrowing"
    )
    user_id = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowing"
    )