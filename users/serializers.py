from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from users.models import Contact
from rest_framework import serializers

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'email', 'password', 'first_name',
                  'last_name', 'address', 'phone_num']
        
class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        ref_name = 'CustomUser'
        fields = ['id', 'email', 'first_name',
                  'last_name', 'address', 'phone_num', 'is_staff']
        read_only_fields = ['is_staff']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'email', 'phone_number', 'comment']

    def validate_phone_number(self, number):
        if not number.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        if len(number) != 11:
            raise serializers.ValidationError("Phone number must be exactly 11 digits.")
        return number

