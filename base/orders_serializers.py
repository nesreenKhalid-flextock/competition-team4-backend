from rest_framework import serializers
from base.models import GroupOrder, GroupOrderItem, GroupOrderParticipant, User, Product


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing orders with basic information
    """

    class Meta:
        model = GroupOrder
        fields = ["id", "name", "status"]


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
