from rest_framework.routers import DefaultRouter
from django.urls import path

from borrowings.views import BorrowingViewSet

router = DefaultRouter()
router.register("borrowings", BorrowingViewSet)

app_name = "borrowings"

urlpatterns = [
    path(
        "borrowings/<int:pk>/return/",
        BorrowingViewSet.as_view({"post": "return_book"}),
        name="return-book"
    )
] + router.urls