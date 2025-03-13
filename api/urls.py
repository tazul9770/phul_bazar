from django.urls import path, include
from rest_framework_nested import routers
from flower.views import FlowerViewSet, CategoryViewSet, ReviewViewSet, FlowerImageViewSet
from order.views import CartViewSet, CartItemViewSet, OrderViewSet


router = routers.DefaultRouter()

router.register('flowers', FlowerViewSet, basename='flowers')
router.register('category', CategoryViewSet)
router.register('carts', CartViewSet, basename='carts')
router.register('orders', OrderViewSet, basename='orders')

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
    path('auth/', include('djoser.urls.jwt'))
]
