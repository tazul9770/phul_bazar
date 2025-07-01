from django.contrib import admin
from flower.models import Flower, Category, Review, FlowerImage

admin.site.register(Flower)
admin.site.register(FlowerImage)
admin.site.register(Category)
admin.site.register(Review)

