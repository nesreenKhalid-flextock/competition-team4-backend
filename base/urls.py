from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from base import users_views, shops_views

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
    ),  # Shop endpoints
    path("shops/", shops_views.ShopListView.as_view(), name="shop_list"),
    path("shops/categories/", shops_views.shop_categories, name="shop_categories"),
    path("shops/<int:pk>/", shops_views.ShopDetailView.as_view(), name="shop_detail"),
    # Product endpoints
    path("shops/<int:shop_id>/products/", shops_views.ProductListView.as_view(), name="product_list"),
    path("products/<int:pk>/", shops_views.ProductDetailView.as_view(), name="product_detail"),
]
