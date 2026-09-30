from django.urls import path, include
from rest_framework_nested import routers
from flower.views import FlowerViewSet, CategoryViewSet, ReviewViewSet, FlowerImageViewSet, MyReviewListAPIView
from order.views import CartViewSet, CartItemViewSet, OrderViewSet, initiate_payment, payment_success, payment_cancel, payment_fail, HasOrderedProduct
from users.views import ContactViewSet
from api import views 

router = routers.DefaultRouter()
router.register('flowers', FlowerViewSet, basename='flowers')
router.register('category', CategoryViewSet)
router.register('carts', CartViewSet, basename='carts')
router.register('orders', OrderViewSet, basename='orders')
router.register('contact', ContactViewSet, basename='contact')

flower_router = routers.NestedDefaultRouter(router, 'flowers', lookup = 'flower')
flower_router.register('reviews', ReviewViewSet, basename='flower-review')
flower_router.register('images', FlowerImageViewSet, basename='product-image')

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_router.register('items', CartItemViewSet, basename='cart-items')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(flower_router.urls)),
    path('', include(cart_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('payment/initiate/', initiate_payment, name="initiate-payment"),
    path('payment/success/', payment_success, name="payment-success"),
    path('payment/cancel/', payment_cancel, name="payment-cancel"),
    path('payment/fail/', payment_fail, name="payment-fail"),
    path("orders/has_ordered/<int:flower_id>/", HasOrderedProduct.as_view()),
    path("dashboard/stats/", views.DashboardStatsView.as_view(), name="dashboard-stats"),
    path("dashboard/orders/latest/", views.LatestOrderView.as_view(), name="latest-order"),
    path("dashboard/my/review/", MyReviewListAPIView.as_view(), name="my-review"),
    path("dashboard/admin/cards/", views.AdminOverviewCardsView.as_view(), name="admin-card"),
    path("dashboard/admin/sales-overview/", views.AdminSalesOverviewView.as_view(), name="admin-sales-overview"),
    path("dashboard/admin/order-status/", views.AdminOrderStatusView.as_view(), name="admin-order-status"),
    path("dashboard/admin/low-stock/", views.AdminLowStockView.as_view(), name="admin-low-stock"),
]
