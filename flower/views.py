from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from flower.models import Flower, Category, Review, FlowerImage
from flower.serializers import FlowerSerializer, CategorySerializer, ReviewSerializer, FlowerImageSerializer
from django.db.models import Count
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from flower.filters import FlowerFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from flower.paginations import DefaultPagination
from api.permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAdminUser, AllowAny, DjangoModelPermissions
from flower.permissions import IsReviewAuthorOrReadonly

class FlowerViewSet(ModelViewSet):
    queryset = Flower.objects.all()
    serializer_class = FlowerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FlowerFilter
    pagination_class = DefaultPagination
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'updated_at']
    permission_classes = [IsAdminOrReadOnly]

class FlowerImageViewSet(ModelViewSet):
    serializer_class = FlowerImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return FlowerImage.objects.filter(flower_id=self.kwargs.get('flower_pk'))

    def perform_create(self, serializer):
        serializer.save(flower_id=self.kwargs.get('flower_pk'))
    
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.annotate(
        flower_count=Count('flowers')).all()
    serializer_class = CategorySerializer

class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewAuthorOrReadonly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        flower_id = self.kwargs.get('flower_pk')
        if not Flower.objects.filter(id=flower_id).exists():
            raise NotFound({"error": f"Flower with ID {flower_id} does not exist."})

        return Review.objects.filter(flower_id=flower_id)

    def get_serializer_context(self):
        flower_id = self.kwargs.get('flower_pk')
        return {'flower_id': flower_id}