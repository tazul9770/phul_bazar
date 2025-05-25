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
from flower.permissions import IsReviewAuthorOrReadonly
from drf_yasg.utils import swagger_auto_schema

class FlowerViewSet(ModelViewSet):

    """
    API endpoint for managing flowers in the e-commerce store
     - Allows authenticated admin to create, update, and delete flowers
     - Allows users to browse and filter flowers
     - Support searching by name, description, and category
     - Support ordering by price and updated_at
    """
    serializer_class = FlowerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FlowerFilter
    pagination_class = DefaultPagination
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'updated_at']
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Flower.objects.prefetch_related('images').all()

    @swagger_auto_schema(
        operation_summary='Retrive a list of flowers'
    )

    def list(self, request, *args, **kwargs):
        """Retrive all the flowers"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Create a flower by admin",
        operation_description="This allow an admin to create a flower",
        request_body=FlowerSerializer,
        responses={
            201: FlowerSerializer,
            400: "Bad Request"
        }
    )
    
    def create(self, request, *args, **kwargs):
        """Only authenticated admin can create flower"""
        return super().create(request, *args, **kwargs)

class FlowerImageViewSet(ModelViewSet):
    serializer_class = FlowerImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return FlowerImage.objects.filter(flower_id=self.kwargs.get('flower_pk'))

    def perform_create(self, serializer):
        serializer.save(flower_id=self.kwargs.get('flower_pk'))
    
class CategoryViewSet(ModelViewSet):
    """
    - Only admin add, delete and update category 
    """
    queryset = Category.objects.annotate(
        flower_count=Count('flowers')).all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewAuthorOrReadonly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        flower_id = self.kwargs.get('flower_pk')
        if not Flower.objects.filter(id=flower_id).exists():
            raise NotFound({"error": f"Flower with ID {flower_id} does not exist."})

        return Review.objects.filter(flower_id=flower_id)

    def get_serializer_context(self):
        flower_id = self.kwargs.get('flower_pk')
        return {'flower_id': flower_id}