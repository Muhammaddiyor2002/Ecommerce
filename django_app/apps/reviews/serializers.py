from __future__ import annotations

from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "product",
            "user",
            "user_email",
            "order",
            "rating",
            "title",
            "body",
            "status",
            "helpful_count",
            "created_at",
        )
        read_only_fields = ("id", "user", "user_email", "status", "helpful_count", "created_at")

    def validate_rating(self, val: int) -> int:
        if not 1 <= val <= 5:
            raise serializers.ValidationError("rating must be 1..5")
        return val
