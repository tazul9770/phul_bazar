from rest_framework import serializers
from order.models import Cart, CartItem, Order, OrderItem
from flower.models import Flower
from order.services import OrderService
from users.models import User

class EmptySerializer(serializers.Serializer):
    pass

class SimpleFlowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flower
        fields = ['id', 'name', 'price']

class AddCartItemSerializer(serializers.ModelSerializer):
    flower_id = serializers.IntegerField()
    class Meta:
        model = CartItem
        fields = ['id', 'flower_id', 'quantity']

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        flower_id = self.validated_data['flower_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(
                cart_id=cart_id, flower_id=flower_id)
            cart_item.quantity += quantity
            self.instance = cart_item.save()
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data)

        return self.instance

    def validate_flower_id(self, value):
        if not Flower.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"Product with id {value} does not exists")
        return value
    
class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

class CartItemSerializer(serializers.ModelSerializer):
    flower = SimpleFlowerSerializer()
    total_price = serializers.SerializerMethodField(method_name='get_total_price')
    class Meta:
        model = CartItem
        fields = ['id', 'flower', 'quantity', 'total_price']

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.flower.price

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total_price')
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']
        read_only_fields = ['user']

    def get_total_price(self, cart: Cart):
        return sum(
            [item.flower.price * item.quantity for item in cart.items.all()])


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart found!')

        if not CartItem.objects.filter(cart_id=cart_id).exists():
            raise serializers.ValidationError('Cart is empty!')

        return cart_id
    
    def create(self, validated_data):
        user_id = self.context['user_id']
        cart_id = validated_data['cart_id']

        try:
            order = OrderService.create_order(user_id=user_id, cart_id=cart_id)
            return order
        except ValueError as e:
            raise serializers.ValidationError(str(e))

    def to_representation(self, instance):
        return OrderSerializer(instance).data

class OrderItemSerializer(serializers.ModelSerializer):
    flower = SimpleFlowerSerializer()
    class Meta:
        model = OrderItem
        fields = ['id', 'flower', 'price', 'quantity', 'total_price']

class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  
        fields = ['id', 'username', 'email', 'address', 'phone_num']

    
class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_price', 'created_at', 'items']