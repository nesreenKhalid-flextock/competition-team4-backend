from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404

from base.enums import GroupOrderStatusEnum
from base.models import GroupOrder, GroupOrderParticipant, GroupOrderItem
from base.orders_serializers import (
    OrderListSerializer,
    OrderDetailsSerializer,
    CreateOrderSerializer,
    AddItemsToOrderSerializer,
    JoinOrderSerializer,
    GroupOrderSummarySerializer,
)
from base.utils import get_user_from_user_auth


class CreateOrderView(generics.CreateAPIView):
    """
    Create a new group order with items
    """

    serializer_class = CreateOrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Create the order
            group_order = serializer.save()

            # Return the created order details
            detail_serializer = OrderDetailsSerializer(group_order)

            return Response(
                {
                    "success": True,
                    "message": "Order created successfully",
                    "data": detail_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JoinOrderView(generics.CreateAPIView):
    """
    Join an existing group order using order code
    """

    serializer_class = JoinOrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)

            # Join the order
            result = serializer.save()

            # Return order details
            detail_serializer = OrderDetailsSerializer(result["order"])

            return Response(
                {
                    "success": True,
                    "message": "Successfully joined the group order",
                    "data": {
                        "order": detail_serializer.data,
                        "participant_id": result["participant"].id,
                        "shop_id": result["shop_id"],
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddItemsToOrderView(generics.CreateAPIView):
    """
    Add items to an existing group order
    """

    serializer_class = AddItemsToOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_order(self):
        """Get the order and check if user can add items to it"""
        order_id = self.kwargs.get("pk")
        order = get_object_or_404(GroupOrder, pk=order_id)
        return order

    def create(self, request, *args, **kwargs):
        try:
            order = self.get_order()

            if order.status != GroupOrderStatusEnum.OPEN.value:
                return Response(
                    {"success": False, "error": "Cannot modify closed orders"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(
                data=request.data, context={"order": order, "request": request}
            )
            serializer.is_valid(raise_exception=True)

            # Add items to the order
            result = serializer.save()

            # Return updated order details
            detail_serializer = OrderDetailsSerializer(result["order"])

            return Response(
                {
                    "success": True,
                    "message": f"Added {len(result['new_items'])} items to order",
                    "data": {
                        "order": detail_serializer.data,
                        "items_added": len(result["new_items"]),
                        "user_total_amount": result["user_total_amount"],
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except GroupOrder.DoesNotExist:
            return Response(
                {"success": False, "error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RemoveItemsFromOrderView(generics.CreateAPIView):
    """
    Remove items from an existing group order
    """

    permission_classes = [IsAuthenticated]

    def get_order(self):
        """Get the order and check if user can remove items from it"""
        order_id = self.kwargs.get("pk")
        order = get_object_or_404(GroupOrder, pk=order_id)
        return order

    def create(self, request, *args, **kwargs):
        try:
            order = self.get_order()

            if order.status != GroupOrderStatusEnum.OPEN.value:
                return Response(
                    {"success": False, "error": "Cannot modify closed orders"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = get_user_from_user_auth(request)

            # Check if order is still open
            if order.status != GroupOrderStatusEnum.OPEN.value:
                return Response(
                    {"success": False, "error": "Cannot modify closed orders"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item_ids = request.data.get("item_ids", [])
            if not item_ids:
                return Response(
                    {"success": False, "error": "No item IDs provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get items to remove (only user's own items)
            items_to_remove = GroupOrderItem.objects.filter(
                id__in=item_ids, group_order=order, user=user
            )

            if not items_to_remove.exists():
                return Response(
                    {"success": False, "error": "No valid items found to remove"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calculate amount to subtract
            removed_amount = sum(item.price * item.quantity for item in items_to_remove)
            removed_count = items_to_remove.count()

            # Remove items
            items_to_remove.delete()

            # Update participant amount and order total
            participant = GroupOrderParticipant.objects.get(
                group_order=order, user=user
            )
            participant.amount -= removed_amount
            participant.save()

            order.total_price -= removed_amount
            order.save()

            # Return updated order details
            detail_serializer = OrderDetailsSerializer(order)

            return Response(
                {
                    "success": True,
                    "message": f"Removed {removed_count} items from order",
                    "data": {
                        "order": detail_serializer.data,
                        "items_removed": removed_count,
                        "amount_reduced": removed_amount,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except GroupOrder.DoesNotExist:
            return Response(
                {"success": False, "error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except GroupOrderParticipant.DoesNotExist:
            return Response(
                {"success": False, "error": "You are not a participant in this order"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UpdateItemQuantityView(generics.UpdateAPIView):
    """
    Update quantity of a specific item in a group order
    """

    permission_classes = [IsAuthenticated]

    def get_object(self):
        item_id = self.kwargs.get("item_id")
        user = get_user_from_user_auth(self.request)
        return get_object_or_404(GroupOrderItem, id=item_id, user=user)

    def update(self, request, *args, **kwargs):
        try:
            item = self.get_object()
            order = item.group_order

            if order.status != GroupOrderStatusEnum.OPEN.value:
                return Response(
                    {"success": False, "error": "Cannot modify closed orders"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = get_user_from_user_auth(request)

            # Check if order is still open
            if order.status != GroupOrderStatusEnum.OPEN.value:
                return Response(
                    {"success": False, "error": "Cannot modify closed orders"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            new_quantity = request.data.get("quantity")
            if new_quantity is None:
                return Response(
                    {"success": False, "error": "Quantity is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                new_quantity = int(new_quantity)
                if new_quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except (ValueError, TypeError):
                return Response(
                    {"success": False, "error": "Quantity must be a positive integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calculate price difference
            old_total = item.price * item.quantity
            new_total = item.price * new_quantity
            price_difference = new_total - old_total

            # Update item quantity
            item.quantity = new_quantity
            item.save()

            # Update participant amount and order total
            participant = GroupOrderParticipant.objects.get(
                group_order=order, user=user
            )
            participant.amount += price_difference
            participant.save()

            order.total_price += price_difference
            order.save()

            # Return updated order details
            detail_serializer = OrderDetailsSerializer(order)

            return Response(
                {
                    "success": True,
                    "message": f"Updated item quantity to {new_quantity}",
                    "data": {
                        "order": detail_serializer.data,
                        "updated_item": {
                            "id": item.id,
                            "product_name": item.product.name,
                            "new_quantity": item.quantity,
                            "price_per_item": item.price,
                            "total_price": item.price * item.quantity,
                        },
                        "price_difference": price_difference,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except GroupOrderItem.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Item not found or you don't own this item",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except GroupOrderParticipant.DoesNotExist:
            return Response(
                {"success": False, "error": "You are not a participant in this order"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OrderListView(generics.ListAPIView):
    """
    List all orders for the authenticated user
    """

    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_user_from_user_auth(self.request)
        queryset = GroupOrder.objects.filter(
            Q(created_by=user) | Q(participants__user=user)
        ).distinct()

        # Filter by status if provided
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search by order name
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                {
                    "success": True,
                    "count": queryset.count(),
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParticipatedOrdersView(generics.ListAPIView):
    """
    List orders that the authenticated user has participated in (not created)
    """

    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_user_from_user_auth(self.request)

        # Get orders where user is a participant but not the creator
        queryset = GroupOrder.objects.filter(participants__user=user).distinct()

        # Filter by status if provided
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search by order name
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                {
                    "success": True,
                    "count": queryset.count(),
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OrderDetailView(generics.RetrieveAPIView):
    """
    Retrieve detailed information about a specific order
    """

    serializer_class = OrderDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_user_from_user_auth(self.request)
        return GroupOrder.objects.filter(
            Q(created_by=user) | Q(participants__user=user)
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        except GroupOrder.DoesNotExist:
            return Response(
                {"success": False, "error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GroupOrderSummaryView(generics.RetrieveAPIView):
    """
    Get detailed summary of a group order with items grouped by user
    """

    serializer_class = GroupOrderSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_user_from_user_auth(self.request)
        # Only allow users who created or participated in the order
        return GroupOrder.objects.filter(
            Q(created_by=user) | Q(participants__user=user)
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={"request": request})
            return Response(
                {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
            )
        except GroupOrder.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Order not found or you don't have permission to view it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LockOrderView(generics.UpdateAPIView):
    """
    Lock a group order - only the creator can lock the order
    """

    permission_classes = [IsAuthenticated]

    def get_object(self):
        order_id = self.kwargs.get("pk")
        user = get_user_from_user_auth(self.request)
        return get_object_or_404(GroupOrder, pk=order_id, created_by=user)

    def update(self, request, *args, **kwargs):
        try:
            order = self.get_object()

            # Check if order is already locked or closed
            if order.status != GroupOrderStatusEnum.OPEN.value:
                return Response(
                    {
                        "success": False,
                        "error": f"Order is already {order.status.lower()}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if order has any items
            if not order.items.exists():
                return Response(
                    {"success": False, "error": "Cannot lock an empty order"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Lock the order by changing status
            order.status = GroupOrderStatusEnum.LOCKED.value
            order.save()

            # Return updated order details
            detail_serializer = OrderDetailsSerializer(order)

            return Response(
                {
                    "success": True,
                    "message": "Order has been locked successfully",
                    "data": detail_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except GroupOrder.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Order not found or you don't have permission to lock it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CancelOrderView(generics.UpdateAPIView):
    """
    Cancel a group order - only the creator can cancel the order
    """

    permission_classes = [IsAuthenticated]

    def get_object(self):
        order_id = self.kwargs.get("pk")
        user = get_user_from_user_auth(self.request)
        return get_object_or_404(GroupOrder, pk=order_id, created_by=user)

    def update(self, request, *args, **kwargs):
        try:
            order = self.get_object()

            # Check if order can be cancelled
            if order.status in [
                GroupOrderStatusEnum.COMPLETED.value,
                GroupOrderStatusEnum.CANCELLED.value,
            ]:
                return Response(
                    {
                        "success": False,
                        "error": f"Cannot cancel an order that is already {order.status.lower()}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Cancel the order
            order.status = GroupOrderStatusEnum.CANCELLED.value
            order.save()

            # Return updated order details
            detail_serializer = OrderDetailsSerializer(order)

            return Response(
                {
                    "success": True,
                    "message": "Order has been cancelled successfully",
                    "data": detail_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except GroupOrder.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Order not found or you don't have permission to cancel it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MarkOrderedView(generics.UpdateAPIView):
    """
    Mark a group order as ordered - only the creator can mark as ordered
    """

    permission_classes = [IsAuthenticated]

    def get_object(self):
        order_id = self.kwargs.get("pk")
        user = get_user_from_user_auth(self.request)
        return get_object_or_404(GroupOrder, pk=order_id, created_by=user)

    def update(self, request, *args, **kwargs):
        try:
            order = self.get_object()

            # Check if order can be marked as ordered
            if order.status != GroupOrderStatusEnum.LOCKED.value:
                return Response(
                    {
                        "success": False,
                        "error": "Only locked orders can be marked as ordered",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Mark as ordered
            order.status = GroupOrderStatusEnum.ORDERED.value
            order.save()

            # Return updated order details
            detail_serializer = OrderDetailsSerializer(order)

            return Response(
                {
                    "success": True,
                    "message": "Order has been marked as ordered successfully",
                    "data": detail_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except GroupOrder.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Order not found or you don't have permission to modify it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CompleteOrderView(generics.UpdateAPIView):
    """
    Complete a group order - only the creator can complete the order
    """

    permission_classes = [IsAuthenticated]

    def get_object(self):
        order_id = self.kwargs.get("pk")
        user = get_user_from_user_auth(self.request)
        return get_object_or_404(GroupOrder, pk=order_id, created_by=user)

    def update(self, request, *args, **kwargs):
        try:
            order = self.get_object()

            # Check if order can be completed
            if order.status not in [
                GroupOrderStatusEnum.ORDERED.value,
                GroupOrderStatusEnum.LOCKED.value,
            ]:
                return Response(
                    {
                        "success": False,
                        "error": "Only ordered or locked orders can be completed",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if order.status == GroupOrderStatusEnum.COMPLETED.value:
                return Response(
                    {
                        "success": False,
                        "error": "Order is already completed",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Complete the order
            order.status = GroupOrderStatusEnum.COMPLETED.value
            order.save()

            # Return updated order details
            detail_serializer = OrderDetailsSerializer(order)

            return Response(
                {
                    "success": True,
                    "message": "Order has been completed successfully",
                    "data": detail_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except GroupOrder.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "Order not found or you don't have permission to complete it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_statuses(request):
    """
    Get all available order statuses
    """
    try:

        statuses = [
            {"value": choice[0], "label": choice[1]}
            for choice in GroupOrderStatusEnum.choices
        ]
        return Response({"success": True, "data": statuses}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
