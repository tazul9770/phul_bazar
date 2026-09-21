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
