from django.shortcuts import render
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from order.models import Cart, CartItem, Order, OrderItem
from order.serializers import CartSerializer, CartItemSerializer, AddCartItemSerializer, UpdateCartItemSerializer, OrderSerializer, CreateOrderSerializer, UpdateOrderSerializer, EmptySerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from order.services import OrderService
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from sslcommerz_lib import SSLCOMMERZ 
from django.conf import settings as main_settings
from django.shortcuts import HttpResponseRedirect
from rest_framework.views import APIView

class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    """
    - Only authenticated user can view Cart
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
        return Cart.objects.prefetch_related('items__flower').filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        existing_cart = Cart.objects.prefetch_related('items__flower').filter(user=request.user).first()

        if existing_cart:
            serializer = self.get_serializer(existing_cart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = CartItemSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer
    
    def get_serializer_context(self):
        return {'cart_id':self.kwargs.get('cart_pk')}

    def get_queryset(self):
        return CartItem.objects.select_related('flower').filter(cart_id=self.kwargs.get('cart_pk'))
    
class OrderViewSet(ModelViewSet):
    """
    - Only authenticated user can create order
    """
    http_method_names = ['get', 'post', 'delete', 'patch', 'head', 'options']

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        OrderService.cancel_order(order=order, user=request.user)
        return Response({'status': 'Order canceled'})
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = UpdateOrderSerializer(
            order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': f'Order status updated to {request.data['status']}'})

    def get_permissions(self):
        if self.action in ['update_status', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'cancel':
            return EmptySerializer
        if self.action == 'create':
            return CreateOrderSerializer
        elif self.action == 'update_status':
            return UpdateOrderSerializer
        return OrderSerializer

    def get_serializer_context(self):
        if getattr(self, 'swagger_fake_view', False):
            return super().get_serializer_context()
        return {'user_id':self.request.user.id, 'user': self.request.user}

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.prefetch_related('items__flower').all()
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.prefetch_related('items__flower').filter(user=self.request.user)

@api_view(['POST'])
def initiate_payment(request):
    user = request.user
    amount = request.data.get("amount")
    order_id = request.data.get("orderId")
    items_num = request.data.get("itemsNum")

    settings = { 'store_id': main_settings.STORE_ID, 'store_pass': main_settings.STORE_PASS, 'issandbox': True }
    sslcz = SSLCOMMERZ(settings)
    post_body = {}
    post_body['total_amount'] = amount
    post_body['currency'] = "BDT"
    post_body['tran_id'] = f"txn_{order_id}"
    post_body['success_url'] = f"{main_settings.BACKEND_URL}/api/v1/payment/success/"
    post_body['fail_url'] = f"{main_settings.BACKEND_URL}/api/v1/payment/fail/"
    post_body['cancel_url'] = f"{main_settings.BACKEND_URL}/api/v1/payment/cancel/"
    post_body['emi_option'] = 0
    post_body['cus_name'] = f"{user.first_name} {user.last_name}"
    post_body['cus_email'] = user.email
    post_body['cus_phone'] = user.phone_num
    post_body['cus_add1'] = user.address
    post_body['cus_city'] = "Dhaka"
    post_body['cus_country'] = "Bangladesh"
    post_body['shipping_method'] = "NO"
    post_body['multi_card_name'] = ""
    post_body['num_of_item'] = items_num
    post_body['product_name'] = "E-commerce products"
    post_body['product_category'] = "General"
    post_body['product_profile'] = "general"


    response = sslcz.createSession(post_body)
    
    if response.get('status') == 'SUCCESS':
        return Response({"payment_url" : response['GatewayPageURL']})
    
    return Response({"error" : "Payment initiation failed!"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def payment_success(request):
    order_id = request.data.get("tran_id").split("_")[1]
    order = Order.objects.get(id=order_id)
    order.status = "Ready to ship"
    order.save()
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/orders/")

@api_view(['POST'])
def payment_cancel(request):
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/orders/")

@api_view(['POST'])
def payment_fail(request):
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/orders/")


class HasOrderedProduct(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, flower_id):
        user = request.user
        has_ordered = OrderItem.objects.filter(order__user = user, flower_id=flower_id).exists()
        return Response({"has_ordered":has_ordered})