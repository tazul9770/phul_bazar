from rest_framework import serializers
from flower.models import Flower, Category, Review
from decimal import Decimal
from rest_framework.exceptions import ValidationError

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name','description', 'flower_count']

    flower_count = serializers.IntegerField(
        read_only=True, help_text="Return the number product in this category")

class FlowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flower
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'price_with_tax', 'image']

    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')

    def calculate_tax(self, product):
        return round(product.price * Decimal(1.1), 2)

    def validate_price(self, price):
        if price < 0:
            raise serializers.ValidationError("Price could not be negative")
        return price
    
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'name', 'description']

    def create(self, validated_data):
        flower_id = self.context.get('flower_id')
        
        if not flower_id:
            raise ValidationError({"flower_id": "Flower ID must be provided."})
        try:
            flower = Flower.objects.get(id=flower_id)
        except Flower.DoesNotExist:
            raise ValidationError({"flower_id": f"Flower with ID {flower_id} does not exist."})

        return Review.objects.create(flower=flower, **validated_data)