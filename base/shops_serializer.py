from rest_framework import serializers
from base.models import Shop, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "description", "image", "category"]


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "name", "address", "description", "menu_image", "category"]


class ShopDetailSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Shop
        fields = ["id", "name", "address", "description", "menu_image", "category", "products"]
