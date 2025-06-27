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
from django.db import models


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

        return {
            "order": order,
            "participant": participant,
            "shop_id": order.shop.id if order.shop else None,
        }


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

    def create(self, validated_data):
        """Create a new group order with items"""

        user = self.context["request"].user.custom_user
        items_data = validated_data.get("items", [])
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

    created_by_me = serializers.SerializerMethodField()

    class Meta:
        model = GroupOrder
        fields = ["id", "name", "status", "code", "created_by_me"]

    def get_created_by_me(self, obj):
        """
        Check if the current user is the creator of the order
        """
        user = get_user_from_user_auth(self.context["request"])
        return obj.created_by == user


class OrderDetailsSerializer(serializers.ModelSerializer):
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


class OrderItemSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for individual order items in summary
    """
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.FloatField(source="product.price", read_only=True)

    class Meta:
        model = GroupOrderItem
        fields = ["product_id" ,"product_name", "product_price", "quantity", "price"]


class UserOrderSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for user summary in group order
    """

    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    items = serializers.SerializerMethodField()
    total_amount = serializers.FloatField(source="amount", read_only=True)
    is_paid = serializers.ReadOnlyField()

    class Meta:
        model = GroupOrderParticipant
        fields = [
            "username",
            "full_name",
            "items",
            "total_amount",
            "paid_amount",
            "delivery_fees",
            "vat",
            "discount",
            "is_paid",
            "payment_method",
        ]

    def get_items(self, obj):
        """Get all items for this user in the order"""
        items = GroupOrderItem.objects.filter(
            group_order=obj.group_order, user=obj.user
        )
        return OrderItemSummarySerializer(items, many=True).data


class GroupOrderSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for group order summary with users and their items
    """

    created_by = serializers.CharField(source="created_by.username", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    shop_address = serializers.CharField(source="shop.address", read_only=True)
    participants = serializers.SerializerMethodField()
    summary_stats = serializers.SerializerMethodField()

    class Meta:
        model = GroupOrder
        fields = [
            "id",
            "name",
            "code",
            "status",
            "created_by",
            "shop_name",
            "shop_address",
            "total_price",
            "delivery_fees",
            "vat",
            "discount",
            "created_at",
            "participants",
            "summary_stats",
        ]

    def get_participants(self, obj):
        """Get all participants with their items"""
        participants = (
            GroupOrderParticipant.objects.filter(group_order=obj)
            .select_related("user")
            .order_by("user__username")
        )

        return UserOrderSummarySerializer(
            participants, many=True, context=self.context
        ).data

    def get_summary_stats(self, obj):
        """Get summary statistics for the order"""
        participants = GroupOrderParticipant.objects.filter(group_order=obj)
        total_items = GroupOrderItem.objects.filter(group_order=obj).count()

        total_paid = sum(p.paid_amount for p in participants)
        total_unpaid = sum(p.amount - p.paid_amount for p in participants)

        return {
            "total_participants": participants.count(),
            "total_items": total_items,
            "total_paid": total_paid,
            "total_unpaid": total_unpaid,
            "fully_paid_users": participants.filter(
                paid_amount__gte=models.F("amount")
            ).count(),
            "unpaid_users": participants.filter(
                paid_amount__lt=models.F("amount")
            ).count(),
        }
