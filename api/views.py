from rest_framework.permissions import IsAuthenticated, IsAdminUser 
from order.models import CartItem, Order
from flower.models import Review
from datetime import timedelta
from decimal import Decimal
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from flower.models import Flower
from users.models import User
from django.db.models.functions import TruncDate


#user dashboard card enpoint 
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

#user latest order 
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


#admin dashboard enpoint 
def pct_change(current, previous):
    """Last 7 days vs ager 7 din. Ager data na thakle None."""
    if not previous:
        return None if not current else 100.0
    return round(float(current - previous) / float(previous) * 100, 1)


def build_card(qs, date_field, total_value=None, sum_field=None):
    """
    qs          : queryset
    date_field  : created_at / date_joined
    sum_field   : deoa thakle Sum, na hole Count
    """
    now = timezone.now()
    week_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)

    def agg(queryset):
        if sum_field:
            return queryset.aggregate(v=Sum(sum_field))["v"] or Decimal("0")
        return queryset.count()

    current = agg(qs.filter(**{f"{date_field}__gte": week_start}))
    previous = agg(qs.filter(**{f"{date_field}__gte": prev_start,
                                f"{date_field}__lt": week_start}))

    # Last 7 diner daily sparkline (data na thakle 0)
    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    metric = Sum(sum_field) if sum_field else Count("id")
    rows = (
        qs.filter(**{f"{date_field}__date__gte": days[0]})
        .annotate(day=TruncDate(date_field))
        .values("day")
        .annotate(v=metric)
    )
    by_day = {r["day"]: r["v"] for r in rows}
    sparkline = [
        {"date": d.isoformat(), "value": float(by_day.get(d) or 0)} for d in days
    ]

    return {
        "total": float(total_value if total_value is not None else agg(qs)),
        "change_percent": pct_change(current, previous),
        "sparkline": sparkline,
    }


class AdminOverviewCardsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        paid_orders = Order.objects.exclude(
            status__in=[Order.CANCELED, Order.NOT_PAID]
        )
        customers = User.objects.filter(is_staff=False)

        return Response({
            "revenue": build_card(
                paid_orders, "created_at", sum_field="total_price",
            ),
            "orders": build_card(Order.objects.all(), "created_at"),
            "customers": build_card(customers, "date_joined"),
            "products": build_card(Flower.objects.all(), "created_at"),
        })

#admin sales overview enpoint create 
RANGE_DAYS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}


class AdminSalesOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        range_key = request.query_params.get("range", "7d")
        days = RANGE_DAYS.get(range_key, 7)

        today = timezone.localdate()
        date_list = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
        start_date = date_list[0]

        paid_orders = Order.objects.exclude(
            status__in=[Order.CANCELED, Order.NOT_PAID]
        ).filter(created_at__date__gte=start_date)

        rows = (
            paid_orders
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("total_price"))
        )
        by_day = {r["day"]: r["total"] for r in rows}

        data = [
            {"date": d.isoformat(), "total": float(by_day.get(d) or 0)}
            for d in date_list
        ]

        return Response({
            "range": range_key,
            "results": data,
        })

#admin dashboard order status enpoint create
STATUS_COLORS = {
    Order.DELIVERED: "#22c55e",      # green
    Order.SHIPPED: "#3b82f6",        # blue
    Order.READY_TO_SHIP: "#f97316",  # orange
    Order.NOT_PAID: "#ec4899",       # pink
    Order.CANCELED: "#9ca3af",       # gray
}

class AdminOrderStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total = Order.objects.count()

        rows = (
            Order.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        breakdown = [
            {
                "status": row["status"],
                "count": row["count"],
                "percent": round(row["count"] / total * 100, 1) if total else 0,
                "color": STATUS_COLORS.get(row["status"], "#9ca3af"),
            }
            for row in rows
        ]

        return Response({
            "total": total,
            "breakdown": breakdown,
        })

#Low stock product 
LOW_STOCK_THRESHOLD = 15

class AdminLowStockView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        flowers = (
            Flower.objects.filter(stock__lte=LOW_STOCK_THRESHOLD)
            .order_by("stock")[:5]
        )

        data = []
        for flower in flowers:
            first_image = flower.images.first()
            data.append({
                "id": flower.id,
                "name": flower.name,
                "stock": flower.stock,
                "image": first_image.image.url if first_image else None,
            })

        return Response(data)