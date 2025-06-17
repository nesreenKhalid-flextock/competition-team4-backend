from rest_framework import serializers
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from base.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=150, required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    instapay_address = serializers.CharField(required=False, allow_blank=True)
    accepted_payment_types = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, allow_empty=True, help_text="List of accepted payment methods"
    )

    class Meta:
        model = AuthUser
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "full_name",
            "phone_number",
            "instapay_address",
            "accepted_payment_types",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        # Remove password_confirm and custom fields from validated_data for AuthUser
        password_confirm = validated_data.pop("password_confirm")
        full_name = validated_data.pop("full_name", "")
        phone_number = validated_data.pop("phone_number", "")
        instapay_address = validated_data.pop("instapay_address", "")
        accepted_payment_types = validated_data.pop("accepted_payment_types", [])

        # Create AuthUser
        auth_user = AuthUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        # Create custom User
        user = User.objects.create(
            auth_user=auth_user,
            username=validated_data["username"],
            full_name=full_name,
            phone_number=phone_number,
            instapay_address=instapay_address,
            accepted_payment_types=accepted_payment_types,
        )

        return auth_user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="Username or email address")
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            # Use the custom authentication backend that allows email or username
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            attrs["user"] = user
        else:
            raise serializers.ValidationError("Must include username/email and password")

        return attrs


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="auth_user.username", read_only=True)
    email = serializers.CharField(source="auth_user.email", read_only=True)
    first_name = serializers.CharField(source="auth_user.first_name", read_only=True)
    last_name = serializers.CharField(source="auth_user.last_name", read_only=True)
    accepted_payment_types = serializers.ListField(
        child=serializers.CharField(max_length=50), read_only=True, help_text="List of accepted payment methods"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "instapay_address",
            "profile_picture",
            "accepted_payment_types",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("New passwords don't match")
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="auth_user.first_name")
    last_name = serializers.CharField(source="auth_user.last_name")
    email = serializers.CharField(source="auth_user.email")
    accepted_payment_types = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, allow_empty=True, help_text="List of accepted payment methods"
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "full_name",
            "phone_number",
            "instapay_address",
            "profile_picture",
            "accepted_payment_types",
        ]

    def update(self, instance, validated_data):
        # Update AuthUser fields
        auth_user_data = validated_data.pop("auth_user", {})
        auth_user = instance.auth_user

        for attr, value in auth_user_data.items():
            setattr(auth_user, attr, value)
        auth_user.save()

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
