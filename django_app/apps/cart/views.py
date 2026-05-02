from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.inventory.services import OutOfStockError

from .serializers import AddItemSerializer, CartSerializer, UpdateItemSerializer
from .services import (
    add_item,
    clear_cart,
    get_or_create_cart,
    remove_item,
    update_item,
)


class CartViewSet(viewsets.ViewSet):
    """A single 'me' cart per user/session.

    Endpoints:
        GET    /cart/                  -> current cart
        POST   /cart/items/            -> add item
        PATCH  /cart/items/{item_id}/  -> update qty
        DELETE /cart/items/{item_id}/  -> remove
        POST   /cart/clear/            -> empty cart
    """

    permission_classes = [AllowAny]

    def _resolve_cart(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        return get_or_create_cart(user=request.user, session_key=session_key)

    def list(self, request):
        cart = self._resolve_cart(request)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="items")
    def add(self, request):
        cart = self._resolve_cart(request)
        ser = AddItemSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            add_item(cart=cart, **ser.validated_data)
        except OutOfStockError as exc:
            return Response(
                {"error": {"code": "out_of_stock", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["patch", "delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def item(self, request, item_id=None):
        cart = self._resolve_cart(request)
        if request.method == "DELETE":
            remove_item(cart=cart, item_id=item_id)
            return Response(CartSerializer(cart).data)
        ser = UpdateItemSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            update_item(cart=cart, item_id=item_id, quantity=ser.validated_data["quantity"])
        except OutOfStockError as exc:
            return Response(
                {"error": {"code": "out_of_stock", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="clear")
    def clear(self, request):
        cart = self._resolve_cart(request)
        clear_cart(cart=cart)
        return Response(CartSerializer(cart).data)
