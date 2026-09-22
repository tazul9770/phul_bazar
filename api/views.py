from django.shortcuts import render
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from order.models import CartItem, Order
from flower.models import Review


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)
        paid_orders = orders.exclude(status__in=[Order.NOT_PAID, Order.CANCELED])
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

        def total(qs):
            return qs.aggregate(t=Sum("total_price"))["t"] or Decimal("0")

        spent_all = total(paid_orders)
        spent_this_month = total(paid_orders.filter(created_at__gte=this_month_start))
        spent_last_month = total(
            paid_orders.filter(created_at__gte=last_month_start, created_at__lt=this_month_start)
        )
        spent_change_percent = (
            round((spent_this_month - spent_last_month) / spent_last_month * 100)
            if spent_last_month
            else None
        )

        items_in_cart = CartItem.objects.filter(cart__user=user).count()
        reviews = Review.objects.filter(user=user)
        reviews_given = reviews.count()
        reviewed_flowers = reviews.values("flower").distinct().count()

        return Response(
            {
                "total_orders": orders.count(),
                "orders_this_month": orders.filter(created_at__gte=this_month_start).count(),
                "items_in_cart": items_in_cart,
                "total_spent": float(spent_all),
                "spent_change_percent": spent_change_percent,
                "reviews_given": reviews_given,
                "reviewed_flowers": reviewed_flowers,
            }
        )


ESTIMATED_DELIVERY_DAYS = 4

STEP_ORDER = [Order.NOT_PAID, Order.READY_TO_SHIP, Order.SHIPPED, Order.DELIVERED]

class LatestOrderView(APIView):
    """
    GET /api/v1/orders/latest/
    Dashboard er "Track your latest order" card er jonno.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = (
            Order.objects.filter(user=request.user)
            .exclude(status=Order.CANCELED)
            .order_by("-created_at")
            .prefetch_related("items__flower")
            .first()
        )

        if not order:
            return Response(None)  # frontend e "No recent orders" dekhabe

        return Response(self._serialize(order))

    def _serialize(self, order):
        current_index = STEP_ORDER.index(order.status)

        steps = []
        for i, status in enumerate(STEP_ORDER):
            if i == 0:
                date = order.created_at
            elif i == current_index:
                date = order.updated_at
            elif i > current_index and status == Order.DELIVERED:
                # Ekhono pouche ni, estimate dekhabo
                date = order.updated_at + timedelta(days=ESTIMATED_DELIVERY_DAYS)
            else:
                # Pass hoye gese kintu real date rakhi ni -> ekhon dekhabo na
                date = None

            steps.append(
                {
                    "status": status,
                    "date": date,
                    "is_estimated": i > current_index and status == Order.DELIVERED,
                    "completed": i < current_index,
                    "current": i == current_index,
                }
            )

        first_item = order.items.first()

        return {
            "id": str(order.id),
            "status": order.status,
            "total_price": float(order.total_price),
            "steps": steps,
            "preview_item": {
                "flower_name": first_item.flower.name if first_item else None,
                "price": float(first_item.price) if first_item else None,
                "image": (
                    first_item.flower.images.first().image.url
                    if first_item and first_item.flower.images.exists()
                    else None
                ),
            } if first_item else None,
        }