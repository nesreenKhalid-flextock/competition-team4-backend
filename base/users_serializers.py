import re
from rest_framework import serializers
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from base.models import User

ACCEPTED_PAYMENT_TYPES_HELP_TEXT = "List of accepted payment methods"

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=150, required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    instapay_address = serializers.CharField(required=False, allow_blank=True)
    accepted_payment_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text=ACCEPTED_PAYMENT_TYPES_HELP_TEXT,
    )

    class Meta:
        model = AuthUser
        fields = [
            "password",
            "password_confirm",
            "full_name",
            "phone_number",
            "instapay_address",
            "accepted_payment_types",
            "username",  # Use phone_number as username if not provided
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match")

        validated_phone_number = self.validate_egyptian_phone_number(
            attrs.get("phone_number", "")
        )

        if AuthUser.objects.filter(username=validated_phone_number).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )

        attrs["phone_number"] = validated_phone_number
        attrs["username"] = validated_phone_number  # <-- Always set username to normalized phone
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password_confirm", None)
        full_name = validated_data.pop("full_name", "")
        phone_number = validated_data.pop("phone_number", "")
        instapay_address = validated_data.pop("instapay_address", "")
        accepted_payment_types = validated_data.pop("accepted_payment_types", [])
        username = validated_data.pop("username")  # This is now always the normalized phone

        fullname_split = full_name.strip().split(maxsplit=1)
        first_name = fullname_split[0] if fullname_split else ""
        last_name = fullname_split[1] if len(fullname_split) > 1 else ""

        auth_user = AuthUser.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        User.objects.create(
            auth_user=auth_user,
            username=username,
            full_name=full_name,
            phone_number=phone_number,
            instapay_address=instapay_address,
            accepted_payment_types=accepted_payment_types,
        )

        return auth_user

    def validate_egyptian_phone_number(self, phone_number: str):
        """
        Validate Egyptian phone numbers
        Accepts formats like: 01121444875, +201121444875, 00201121444875
        """
        if not phone_number:
            raise serializers.ValidationError("Phone number is required.")

        # Remove any spaces, dashes, or parentheses
        cleaned_phone = re.sub(r"[\s\-\(\)]", "", phone_number)

        # Egyptian mobile number patterns
        patterns = [
            r"^(01)[0125]\d{8}$",  # 01X XXXXXXXX (Egyptian local format)
            r"^(\+20|0020|20)(1)[0125]\d{8}$",  # +20 1X XXXXXXXX (International format)
        ]

        # Check if the phone number matches any of the patterns
        is_valid = any(re.match(pattern, cleaned_phone) for pattern in patterns)

        if not is_valid:
            raise serializers.ValidationError(
                "Please enter a valid Egyptian mobile number. "
                "Format: 01X XXXXXXXX (where X is 0, 1, 2, or 5 for the second digit)"
            )

        # Normalize to international format
        if cleaned_phone.startswith("00"):
            normalized_phone = "+" + cleaned_phone[2:]
        elif cleaned_phone.startswith("20"):
            normalized_phone = "+" + cleaned_phone
        elif cleaned_phone.startswith("01"):
            normalized_phone = "+20" + cleaned_phone[1:]
        elif cleaned_phone.startswith("+20"):
            normalized_phone = cleaned_phone
        else:
            raise serializers.ValidationError(
                "Please enter a valid Egyptian mobile number. "
                "Format: 01X XXXXXXXX (where X is 0, 1, 2, or 5 for the second digit)"
            )
        return normalized_phone

class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(help_text="Phone Number")
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")

        if phone_number and password:
            normalized_phone = UserRegistrationSerializer().validate_egyptian_phone_number(phone_number)
            # Ensure username is the normalized phone number as used in registration
            user = authenticate(username=normalized_phone, password=password)
            if not user:
                # Try fallback: check if user exists with normalized_phone as username
                if AuthUser.objects.filter(username=normalized_phone).exists():
                    raise serializers.ValidationError({"non_field_errors": ["Invalid credentials"]})
                else:
                    raise serializers.ValidationError({"non_field_errors": ["User does not exist"]})
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            attrs["user"] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include 'phone_number' and 'password'.")

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="auth_user.username", read_only=True)
    username = serializers.CharField(source="auth_user.username", read_only=True)
    email = serializers.CharField(source="auth_user.email", read_only=True)
    first_name = serializers.CharField(source="auth_user.first_name", read_only=True)
    last_name = serializers.CharField(source="auth_user.last_name", read_only=True)
    accepted_payment_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        read_only=True,
        help_text=ACCEPTED_PAYMENT_TYPES_HELP_TEXT,
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
            "accepted_payment_types",
        ]
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("New password and confirm password do not match.")
        return attrs

class UpdateProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="auth_user.first_name")
    last_name = serializers.CharField(source="auth_user.last_name")
    email = serializers.CharField(source="auth_user.email")
    accepted_payment_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text=ACCEPTED_PAYMENT_TYPES_HELP_TEXT,
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