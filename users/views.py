from rest_framework.viewsets import ModelViewSet
from users.serializers import ContactSerializer
from users.models import Contact
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from users.pagination import CustomPagination
from djoser.views import UserViewSet

class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPagination

class ContactView(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user_email = serializer.validated_data['email']
            user_msg = serializer.validated_data['write_something']
            number = serializer.validated_data['phone_number']
            send_mail(
                subject="Welcome to Phul_Bazar",
                message='Thank you for reaching out! I will get back to you shortly.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user_email],
                fail_silently=False,
            )
            send_mail(
                subject="Phul_Bazar Customer send mail",
                message=f"{number}\n\n{user_email}\n\n{user_msg}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

