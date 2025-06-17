from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import authenticate

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UpdateProfileSerializer,
)
from .models import User


class RegisterView(generics.CreateAPIView):
    queryset = AuthUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Get user profile data
        user_profile = User.objects.get(auth_user=user)
        user_data = UserSerializer(user_profile).data

        return Response(
            {
                "message": "User registered successfully",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(access_token),
                },
                "user": user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Get user profile data
        try:
            user_profile = User.objects.get(auth_user=user)
            user_data = UserSerializer(user_profile).data
        except User.DoesNotExist:
            # Create profile if it doesn't exist
            user_profile = User.objects.create(auth_user=user, username=user.username)
            user_data = UserSerializer(user_profile).data

        return Response(
            {
                "message": "Login successful",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(access_token),
                },
                "user": user_data,
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return User.objects.get(auth_user=self.request.user)
        except User.DoesNotExist:
            # Create profile if it doesn't exist
            return User.objects.create(
                auth_user=self.request.user, username=self.request.user.username
            )


class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return User.objects.get(auth_user=self.request.user)
        except User.DoesNotExist:
            # Create profile if it doesn't exist
            return User.objects.create(
                auth_user=self.request.user, username=self.request.user.username
            )


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response(
        {"status": "API is running", "message": "Group Ordering API is healthy"},
        status=status.HTTP_200_OK,
    )
