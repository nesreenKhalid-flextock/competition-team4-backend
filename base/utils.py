import random
import string
import re

from django.http import HttpRequest
from django.contrib.auth.models import User as AuthUser
from rest_framework import serializers

from base.models import User


def get_user_from_user_auth(request: HttpRequest):
    auth_user = request.user
    return User.objects.get(auth_user=auth_user)


def generate_unique_order_code():
    """Generate a unique 6-digit alphanumeric code for orders"""
    from base.models import GroupOrder

    while True:
        # Generate a 6-digit code using numbers and uppercase letters
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Check if this code already exists
        if not GroupOrder.objects.filter(code=code).exists():
            return code
