from datetime import date
from decimal import Decimal

from django.db import models


class Payment(models.Model):
    FINE_MULTIPLIER = 2
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"

    class TypeChoices(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(
        choices=StatusChoices.choices,
        max_length=20,
    )
    type = models.CharField(
        choices=TypeChoices.choices,
        max_length=20,
    )
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=5, decimal_places=2)

    def calculate_money_to_pay(
            self,
            date_of_borrowing: date,
            date_of_return: date,
            daily_fee: Decimal,
    ) -> Decimal:
        days_borrowed = (date_of_return - date_of_borrowing).days
        total_cost = days_borrowed * daily_fee
        return total_cost.quantize(Decimal("0.01"))

    def calculate_fine(
            self,
            expected_return_date: date,
            actual_return_date: date,
            daily_fee: Decimal,
    )-> Decimal:
        if actual_return_date > expected_return_date:
            overdue_days = (actual_return_date-expected_return_date).days
            fine = overdue_days * daily_fee * self.FINE_MULTIPLIER
            return fine.quantize(Decimal("0.01"))
        return Decimal("0.00")