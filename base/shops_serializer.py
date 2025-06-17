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
    product_categories = serializers.SerializerMethodField()

    def get_product_categories(self, shop):
        # Get distinct categories from products in this shop
        categories = shop.products.exclude(category__isnull=True).exclude(category__exact="").values_list("category", flat=True).distinct()
        return list(categories)

    class Meta:
        model = Shop
        fields = ["id", "name", "address", "description", "menu_image", "category", "products", "product_categories"]
