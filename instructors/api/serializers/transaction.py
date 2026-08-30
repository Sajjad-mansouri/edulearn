# serializers.py
from rest_framework import serializers

from payments.models import Payment


class TransactionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    course = serializers.CharField(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "type", "amount", "date", "status", "course"]

    def get_type(self, obj):
        return "sale"

    def get_date(self, obj):
        if obj.status == Payment.Status.SUCCEEDED and obj.paid_at:
            return obj.paid_at
        if obj.status == Payment.Status.REFUNDED and obj.refunded_at:
            return obj.refunded_at
        return obj.updated_at
