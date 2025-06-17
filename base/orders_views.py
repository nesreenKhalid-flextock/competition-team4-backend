from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404

from base.enums import GroupOrderStatusEnum
from base.models import GroupOrder
from base.orders_serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    CreateOrderSerializer,
    AddItemsToOrderSerializer,
    JoinOrderSerializer,
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
            detail_serializer = OrderDetailSerializer(group_order)

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
            detail_serializer = OrderDetailSerializer(result["order"])

            return Response(
                {
                    "success": True,
                    "message": "Successfully joined the group order",
                    "data": {
                        "order": detail_serializer.data,
                        "participant_id": result["participant"].id,
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

            serializer = self.get_serializer(
                data=request.data, context={"order": order, "request": request}
            )
            serializer.is_valid(raise_exception=True)

            # Add items to the order
            result = serializer.save()

            # Return updated order details
            detail_serializer = OrderDetailSerializer(result["order"])

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

    serializer_class = OrderDetailSerializer
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
