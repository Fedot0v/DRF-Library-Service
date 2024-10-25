from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "session_url",
            "session_id",
            "money_to_pay"
        )


class PaymentListSerializer(PaymentSerializer):
    class Meta(PaymentSerializer.Meta):
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "money_to_pay",
        )
