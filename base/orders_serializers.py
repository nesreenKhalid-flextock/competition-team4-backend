from rest_framework import serializers
from base.models import (
    GroupOrder,
    GroupOrderItem,
    GroupOrderParticipant,
    User,
    Product,
    Shop,
)
from base.enums import GroupOrderStatusEnum
from base.utils import get_user_from_user_auth, generate_unique_order_code


class OrderItemCreateSerializer(serializers.Serializer):
    """
    Serializer for creating order items
    """

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class JoinOrderSerializer(serializers.Serializer):
    """
    Serializer for joining an existing order using order code
    """

    code = serializers.CharField(max_length=6)

    def validate_code(self, value):
        """Validate that the order code exists and is joinable"""
        try:
            order = GroupOrder.objects.get(code=value)
        except GroupOrder.DoesNotExist:
            raise serializers.ValidationError("Invalid order code")

        if order.status != GroupOrderStatusEnum.OPEN.value:
            raise serializers.ValidationError(
                "This order is no longer accepting new participants"
            )

        return value

    def validate(self, attrs):
        """Additional validation to check if user is already a participant"""
        code = attrs["code"]
        user = get_user_from_user_auth(self.context["request"])
        order = GroupOrder.objects.get(code=code)

        # Check if user is already a participant
        if GroupOrderParticipant.objects.filter(group_order=order, user=user).exists():
            raise serializers.ValidationError(
                "You are already a participant in this order"
            )

        return attrs

    def create(self, validated_data):
        """Add user as participant to the order"""
        code = validated_data["code"]
        user = get_user_from_user_auth(self.context["request"])
        order = GroupOrder.objects.get(code=code)

        # Create participant entry with zero initial amount
        participant = GroupOrderParticipant.objects.create(
            group_order=order,
            user=user,
            amount=0.0,
            delivery_fees=0.0,
            vat=0.0,
            discount=0.0,
        )

        return {"order": order, "participant": participant}


class AddItemsToOrderSerializer(serializers.Serializer):
    """
    Serializer for adding items to an existing order
    """

    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        """Validate that all products exist and belong to the order's shop"""
        if not value:
            raise serializers.ValidationError("At least one item is required")

        order = self.context["order"]
        product_ids = [item["product_id"] for item in value]
        products = Product.objects.filter(id__in=product_ids, shop=order.shop)

        if len(products) != len(product_ids):
            raise serializers.ValidationError(
                "One or more products not found or don't belong to this shop"
            )

        return value

    def validate(self, attrs):
        """Validate that the order is still open"""
        order = self.context["order"]
        if order.status != GroupOrderStatusEnum.OPEN.value:
            raise serializers.ValidationError("Cannot add items to a closed order")
        return attrs

    def create(self, validated_data):
        """Add items to the existing order"""
        order = self.context["order"]
        user = get_user_from_user_auth(self.context["request"])
        items_data = validated_data["items"]

        # Get products
        product_ids = [item["product_id"] for item in items_data]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

        # Calculate user's additional amount
        user_additional_amount = 0
        new_items = []

        for item_data in items_data:
            product = products[item_data["product_id"]]
            item_total_price = product.price * item_data["quantity"]
            user_additional_amount += item_total_price

            # Create order item
            order_item = GroupOrderItem.objects.create(
                group_order=order,
                product=product,
                user=user,
                quantity=item_data["quantity"],
                price=item_total_price,
            )
            new_items.append(order_item)

        # Update order total price
        order.total_price += user_additional_amount
        order.save()

        # Update or create participant entry
        participant, created = GroupOrderParticipant.objects.get_or_create(
            group_order=order,
            user=user,
            defaults={
                "amount": user_additional_amount,
                "delivery_fees": 0.0,
                "vat": 0.0,
                "discount": 0.0,
            },
        )

        if not created:
            # Update existing participant
            participant.amount += user_additional_amount
            participant.save()

        return {
            "order": order,
            "new_items": new_items,
            "user_total_amount": participant.amount,
        }


class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer for creating a new order with items
    """

    name = serializers.CharField(required=False, max_length=255)
    shop_id = serializers.IntegerField()
    items = OrderItemCreateSerializer(required=False, many=True)
    delivery_fees = serializers.FloatField(required=False, default=0.0)
    vat = serializers.FloatField(required=False, default=0.0)
    discount = serializers.FloatField(required=False, default=0.0)

    def validate_shop_id(self, value):
        """Validate that the shop exists"""

        try:
            Shop.objects.get(id=value)
        except Shop.DoesNotExist:
            raise serializers.ValidationError("Shop not found")
        return value

    def validate_items(self, value):
        """Validate that all products exist and belong to the same shop"""
        if not value:
            raise serializers.ValidationError("At least one item is required")

        product_ids = [item["product_id"] for item in value]
        products = Product.objects.filter(id__in=product_ids)

        if len(products) != len(product_ids):
            raise serializers.ValidationError("One or more products not found")

        return value

    def create(self, validated_data):
        """Create a new group order with items"""

        user = self.context["request"].user.custom_user
        items_data = validated_data.pop("items")
        shop = Shop.objects.get(id=validated_data["shop_id"])

        # Calculate total price
        total_price = 0
        product_ids = [item["product_id"] for item in items_data]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

        for item in items_data:
            product = products[item["product_id"]]
            total_price += product.price * item["quantity"]

        # Add fees and taxes
        total_price += validated_data.get("delivery_fees", 0)
        total_price += validated_data.get("vat", 0)
        total_price -= validated_data.get("discount", 0)

        # Generate unique order code
        order_code = generate_unique_order_code()

        # Create the group order
        group_order = GroupOrder.objects.create(
            name=validated_data["name"],
            created_by=user,
            shop=shop,
            total_price=total_price,
            delivery_fees=validated_data.get("delivery_fees", 0),
            vat=validated_data.get("vat", 0),
            discount=validated_data.get("discount", 0),
            status=GroupOrderStatusEnum.OPEN.value,
            code=order_code,
        )

        # Create order items
        for item_data in items_data:
            product = products[item_data["product_id"]]
            GroupOrderItem.objects.create(
                group_order=group_order,
                product=product,
                user=user,
                quantity=item_data["quantity"],
                price=product.price * item_data["quantity"],
            )

        # Create participant entry for the creator
        participant_amount = sum(
            products[item["product_id"]].price * item["quantity"] for item in items_data
        )

        GroupOrderParticipant.objects.create(
            group_order=group_order,
            user=user,
            amount=participant_amount,
            delivery_fees=validated_data.get("delivery_fees", 0)
            / 1,  # Will be split among participants
            vat=validated_data.get("vat", 0) / 1,
            discount=validated_data.get("discount", 0) / 1,
        )

        return group_order


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing orders with basic information
    """

    class Meta:
        model = GroupOrder
        fields = ["id", "name", "status", "code"]


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed order information
    """

    created_by = serializers.CharField(source="created_by.username", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    items_count = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = GroupOrder
        fields = [
            "id",
            "name",
            "status",
            "code",
            "total_price",
            "delivery_fees",
            "vat",
            "discount",
            "created_at",
            "updated_at",
            "created_by",
            "shop_name",
            "items_count",
            "participants_count",
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_participants_count(self, obj):
        return obj.participants.count()
