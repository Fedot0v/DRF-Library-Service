from rest_framework.routers import DefaultRouter

from payments import views

router = DefaultRouter()

router.register("payments", views.PaymentViewSet)

app_name = "payments"

urlpatterns = router.urls
