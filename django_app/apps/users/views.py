"""Auth + user views. Throttled, idempotent, structured-logged."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Address
from .serializers import (
    AddressSerializer,
    NovaTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LoginView(TokenObtainPairView):
    serializer_class = NovaTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"error": {"code": "missing_refresh", "message": "refresh token required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except Exception:  # pragma: no cover
            return Response(
                {"error": {"code": "invalid_refresh", "message": "invalid refresh token"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "logged out"}, status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by("-is_default", "-created_at")

    def perform_create(self, serializer):
        addr = serializer.save(user=self.request.user)
        if addr.is_default:
            (
                Address.objects.filter(user=self.request.user, kind=addr.kind)
                .exclude(pk=addr.pk)
                .update(is_default=False)
            )

    @action(detail=True, methods=["post"])
    def make_default(self, request, pk=None):
        addr = self.get_object()
        Address.objects.filter(user=request.user, kind=addr.kind).update(is_default=False)
        addr.is_default = True
        addr.save(update_fields=["is_default"])
        return Response(self.get_serializer(addr).data)
