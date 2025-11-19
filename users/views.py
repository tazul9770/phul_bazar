from rest_framework.viewsets import ModelViewSet
from users.serializers import ContactSerializer
from users.models import Contact
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from users.pagination import CustomPagination


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # Send welcome email to the user
            user_email = serializer.data['email']
            user_msg = serializer.data['comment']

            send_mail(
                subject='Welcome to Our Phul Bazar!',
                message='Thank you for reaching out! We will get back to you shortly.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user_email],
                fail_silently=False,
            )

            send_mail(
                subject="Customer send message",
                message=f"{user_email} send you message\n\n{user_msg}",
                from_email=user_email,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)