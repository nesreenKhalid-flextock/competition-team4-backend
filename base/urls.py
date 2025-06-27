from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from base import users_views, shops_views, orders_views

urlpatterns = [
    # Health check
    path("health/", users_views.health_check, name="health_check"),
    # Authentication endpoints
    path("auth/register/", users_views.RegisterView.as_view(), name="register"),
    path("auth/login/", users_views.LoginView.as_view(), name="login"),
    path("auth/logout/", users_views.logout_view, name="logout"),
    # JWT token endpoints
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # User profile endpoints
    path("auth/profile/", users_views.ProfileView.as_view(), name="profile"),
    path(
        "auth/profile/update/",
        users_views.UpdateProfileView.as_view(),
        name="update_profile",
    ),
    path(
        "auth/change-password/",
        users_views.ChangePasswordView.as_view(),
        name="change_password",
    ),
    # Payment methods endpoint
    path(
        "auth/payment-methods/", users_views.get_payment_methods, name="payment_methods"
    ),
    # Shop endpoints
    path("shops/", shops_views.ShopListView.as_view(), name="shop_list"),
    path("shops/categories/", shops_views.shop_categories, name="shop_categories"),
    path("shops/<int:pk>/", shops_views.ShopDetailView.as_view(), name="shop_detail"),
    path("shops/create-by-name/", shops_views.create_shop_by_name, name="create_shop_by_name"),
    # Product endpoints
    path(
        "products/categories/",
        shops_views.product_categories,
        name="product_categories",
    ),
    path(
        "shops/<int:shop_id>/products/",
        shops_views.ProductListView.as_view(),
        name="product_list",
    ),
    path(
        "products/<int:pk>/",
        shops_views.ProductDetailView.as_view(),
        name="product_detail",
    ),
    # Order endpoints
    path("orders/", orders_views.OrderListView.as_view(), name="order_list"),
    path("orders/create/", orders_views.CreateOrderView.as_view(), name="create_order"),
    path("orders/join/", orders_views.JoinOrderView.as_view(), name="join_order"),
    path(
        "orders/participated/",
        orders_views.ParticipatedOrdersView.as_view(),
        name="participated_orders",
    ),
    path(
        "orders/<int:pk>/", orders_views.OrderDetailView.as_view(), name="order_detail"
    ),
    path(
        "orders/<int:pk>/summary/",
        orders_views.GroupOrderSummaryView.as_view(),
        name="group_order_summary",
    ),
    path(
        "orders/<int:pk>/add-items/",
        orders_views.AddItemsToOrderView.as_view(),
        name="add_items_to_order",
    ),
    path(
        "orders/<int:pk>/remove-items/",
        orders_views.RemoveItemsFromOrderView.as_view(),
        name="remove_items_from_order",
    ),
    path(
        "orders/items/<int:item_id>/update-quantity/",
        orders_views.UpdateItemQuantityView.as_view(),
        name="update_item_quantity",
    ),
    path(
        "orders/<int:pk>/lock/",
        orders_views.LockOrderView.as_view(),
        name="lock_order",
    ),
    path(
        "orders/<int:pk>/cancel/",
        orders_views.CancelOrderView.as_view(),
        name="cancel_order",
    ),
    path(
        "orders/<int:pk>/mark-ordered/",
        orders_views.MarkOrderedView.as_view(),
        name="mark_ordered",
    ),
    path(
        "orders/<int:pk>/complete/",
        orders_views.CompleteOrderView.as_view(),
        name="complete_order",
    ),
    path("orders/statuses/", orders_views.order_statuses, name="order_statuses"),
]
