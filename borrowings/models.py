from django.db import models
from rest_framework.exceptions import ValidationError

from books.models import Book
from library_service import settings


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrowings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    expected_return_date__gt=models.F("borrow_date")
                ),
                name="expected_return_date_after_borrow_date"
            ),
            models.CheckConstraint(
                check=models.Q(
                    actual_return_date__gte=models.F("borrow_date")
                )
                      | models.Q(actual_return_date__isnull=True),
                name="actual_return_date_after_borrow_date_or_null"
            ),
        ]

    def clean(self):
        if self.book.inventory <= 0:
            raise ValidationError("This book is currently not available.")

        if self.expected_return_date \
                and self.expected_return_date <= self.borrow_date:
            raise ValidationError(
                "Expected return date must be later than borrowing date."
            )

        if self.actual_return_date \
                and self.actual_return_date >= self.borrow_date:
            raise ValidationError(
                "Actual return date must be later than borrowing date."
            )

        if self.pk and self.actual_return_date is not None:
            raise ValidationError("This book has already been returned.")


    def save(self, *args, **kwargs):
        if self.actual_return_date:
            self.book.inventory += 1

        elif not self.pk:
            self.book.inventory -= 1

        self.book.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} borrowed {self.book} on {self.borrow_date}"
