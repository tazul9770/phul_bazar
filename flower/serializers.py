from rest_framework import serializers
from flower.models import Flower, Category, Review, FlowerImage
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name','description', 'flower_count']

    flower_count = serializers.IntegerField(
        read_only=True, help_text="Return the number product in this category")
    
class FlowerImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()
    class Meta:
        model = FlowerImage
        fields = ['id', 'image']

class FlowerSerializer(serializers.ModelSerializer):
    images = FlowerImageSerializer(many=True, read_only=True)
    class Meta:
        model = Flower
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'price_with_tax', 'images']

    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')

    def calculate_tax(self, product):
        return round(product.price * Decimal(1.1), 2)

    def validate_price(self, price):
        if price < 0:
            raise serializers.ValidationError("Price could not be negative")
        return price
    
class SimpleUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(
        method_name='get_current_user_name')

    class Meta:
        model = get_user_model()
        fields = ['id', 'name']

    def get_current_user_name(self, obj):
        return obj.get_full_name()
    
class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(method_name='get_user')
    class Meta:
        model = Review
        fields = ['id', 'flower', 'user', 'ratings', 'comment']
        read_only_fields = ['user', 'flower']

    def get_user(self, obj):
        return SimpleUserSerializer(obj.user).data

    def create(self, validated_data):
        flower_id = self.context.get('flower_id')
        
        if not flower_id:
            raise ValidationError({"flower_id": "Flower ID must be provided."})
        try:
            flower = Flower.objects.get(id=flower_id)
        except Flower.DoesNotExist:
            raise ValidationError({"flower_id": f"Flower with ID {flower_id} does not exist."})

        return Review.objects.create(flower=flower, **validated_data)