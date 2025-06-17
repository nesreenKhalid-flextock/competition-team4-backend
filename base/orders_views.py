from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from base.enums import GroupOrderStatusEnum
from base.models import GroupOrder, User
from base.orders_serializers import OrderListSerializer, OrderDetailSerializer
from base.utils import get_user_from_user_auth


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
