from __future__ import annotations

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Review.objects.select_related("user", "product").order_by("-created_at")
        if self.action in {"list", "retrieve"}:
            qs = qs.filter(status=Review.Status.APPROVED)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status=Review.Status.PENDING)
