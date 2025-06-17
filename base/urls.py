from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

urlpatterns = [
    # Health check
    path("health/", views.health_check, name="health_check"),
    # Authentication endpoints
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    # JWT token endpoints
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # User profile endpoints
    path("auth/profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "auth/profile/update/", views.UpdateProfileView.as_view(), name="update_profile"
    ),
    path(
        "auth/change-password/",
        views.ChangePasswordView.as_view(),
        name="change_password",
    ),
]
