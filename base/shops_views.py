from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q

from base.models import Shop, Product
from base.shops_serializer import ShopSerializer, ShopDetailSerializer, ProductSerializer

# List all shops with optional filtering by category and search
class ShopListView(generics.ListAPIView):
    """
    List all shops with optional filtering by category and search
    """

    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]

    # Get filtered queryset for shops
    def get_queryset(self):
        queryset = Shop.objects.all()

        # Filter by category if provided
        category = self.request.query_params.get("category", None)
        if category:
            queryset = queryset.filter(category=category)

        # Search by name or description
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

        return queryset.order_by("name")

    # Return list of shops with success/error response
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({"success": True, "count": queryset.count(), "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Retrieve a shop with its products
class ShopDetailView(generics.RetrieveAPIView):
    """
    Retrieve a shop with its products
    """

    queryset = Shop.objects.all()
    serializer_class = ShopDetailSerializer
    permission_classes = [IsAuthenticated]

    # Retrieve a single shop by pk with error handling
    def retrieve(self, request, *args, **kwargs):
        try:
            # Explicitly handle the pk lookup to check if shop exists
            pk = kwargs.get("pk")
            shop = get_object_or_404(Shop, pk=pk)
            serializer = self.get_serializer(shop)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Shop.DoesNotExist:
            return Response({"success": False, "error": f"Shop with ID {kwargs.get('pk')} not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# List all products for a shop or create a new product
class ProductListView(generics.ListCreateAPIView):
    """
    List all products for a shop or create a new product
    """

    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    # Get filtered queryset for products of a shop
    def get_queryset(self):
        shop_id = self.kwargs.get("shop_id")
        queryset = Product.objects.filter(shop_id=shop_id)

        # Filter by category if provided
        category = self.request.query_params.get("category", None)
        if category:
            queryset = queryset.filter(category__icontains=category)

        # Search products by name
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("name")

    # Return list of products for a shop with success/error response
    def list(self, request, *args, **kwargs):
        try:
            shop_id = self.kwargs.get("shop_id")
            # Verify shop exists
            get_object_or_404(Shop, pk=shop_id)

            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({"success": True, "shop_id": shop_id, "count": queryset.count(), "data": serializer.data}, status=status.HTTP_200_OK)
        except Shop.DoesNotExist:
            return Response({"success": False, "error": "Shop not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Save a new product for a shop
    def perform_create(self, serializer):
        shop_id = self.kwargs.get("shop_id")
        shop = get_object_or_404(Shop, pk=shop_id)
        serializer.save(shop=shop)

    # Create a new product for a shop with error handling
    def create(self, request, *args, **kwargs):
        try:
            shop_id = self.kwargs.get("shop_id")
            # Verify shop exists
            get_object_or_404(Shop, pk=shop_id)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response({"success": True, "message": "Product created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        except Shop.DoesNotExist:
            return Response({"success": False, "error": "Shop not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Retrieve, update or delete a product
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    # Retrieve a single product by pk with error handling
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"success": False, "error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Update a product with error handling
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response({"success": True, "message": "Product updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"success": False, "error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Delete a product with error handling
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            product_name = instance.name
            self.perform_destroy(instance)
            return Response({"success": True, "message": f'Product "{product_name}" deleted successfully'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"success": False, "error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Get all distinct product categories currently in use
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def product_categories(request):
    """
    Get all distinct product categories currently in use
    """
    try:
        # Get distinct categories that are not null or empty
        categories = Product.objects.filter(category__isnull=False).exclude(category__exact="").values_list("category", flat=True).distinct()

        categories_list = [cat for cat in categories if cat]
        return Response({"success": True, "data": categories_list}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Get all available shop categories
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def shop_categories(request):
    """
    Get all available shop categories
    """
    try:

        categories = [{"value": choice[0], "label": choice[1]} for choice in ShopCategoryEnum.choices]
        return Response({"success": True, "data": categories}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """
    Get all available shop categories
    """
    try:
        from base.enums import ShopCategoryEnum

        categories = [{"value": choice[0], "label": choice[1]} for choice in ShopCategoryEnum.choices]
        return Response({"success": True, "data": categories}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_shop_by_name(request):
    """
    Create a shop with only a name (other fields blank/default)
    """
    name = request.data.get("name")
    if not name:
        return Response({"success": False, "error": "Name is required."}, status=status.HTTP_400_BAD_REQUEST)

    from base.models import Shop
    shop = Shop.objects.create(
        name=name,
        description="",
        category="SUPERMARKET",  # or any default valid category
        address="",
    )
    from base.shops_serializer import ShopSerializer
    serializer = ShopSerializer(shop)
    return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)
