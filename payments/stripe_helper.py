from django.urls import reverse

import stripe
from django.conf import settings
from django.utils import timezone

from payments.models import Payment


stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_session(borrowing, request):
    book = borrowing.book
    daily_fee = book.daily_fee
    expected_return_date = borrowing.expected_return_date
    actual_return_date = borrowing.actual_return_date

    money_to_pay = Payment().calculate_money_to_pay(
        date_of_borrowing=borrowing.borrow_date,
        date_of_return=actual_return_date or timezone.now(),
        daily_fee=daily_fee,
    )

    fine = Payment().calculate_fine(
        expected_return_date=expected_return_date,
        actual_return_date=actual_return_date or timezone.now(),
        daily_fee=daily_fee,
    )

    total_money_to_pay = money_to_pay + fine

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Borrowing of {book.title}",
                },
                "unit_amount": int(total_money_to_pay * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.build_absolute_uri(
            reverse("payments:payment-success", kwargs={"pk": 0})
        ),
        cancel_url=request.build_absolute_uri(reverse(
            "payments:payment-cancel", kwargs={"pk": 0})
        ),
    )

    payment = Payment.objects.create(
        status=Payment.StatusChoices.PENDING,
        type=Payment.TypeChoices.PAYMENT,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=total_money_to_pay,
    )

    return session.url, session.id