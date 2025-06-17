from django.http import HttpRequest

from base.models import User


def get_user_from_user_auth(request: HttpRequest):
    auth_user = request.user
    return User.objects.get(auth_user=auth_user)
