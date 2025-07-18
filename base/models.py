from django.db import models
from django.contrib.auth.models import User as AuthUser
import json

from base.enums import (
    GroupOrderStatusEnum,
    ShopCategoryEnum,
    UserAcceptedPaymentMethodsEnum,
)


class User(models.Model):
    auth_user = models.OneToOneField(
        AuthUser, on_delete=models.CASCADE, related_name="custom_user"
    )
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    instapay_address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    accepted_payment_types = models.JSONField(
        default=list, blank=True, help_text="List of accepted payment methods"
    )

    def set_accepted_payment_types(self, payment_types):
        """Set accepted payment types from a list of strings"""
        if isinstance(payment_types, list):
            self.accepted_payment_types = payment_types
        elif isinstance(payment_types, str):
            # Handle comma-separated string input
            self.accepted_payment_types = [
                pt.strip() for pt in payment_types.split(",") if pt.strip()
            ]
        else:
            self.accepted_payment_types = []

    def get_accepted_payment_types(self):
        """Get accepted payment types as a list"""
        if isinstance(self.accepted_payment_types, list):
            return self.accepted_payment_types
        elif isinstance(self.accepted_payment_types, str):
            return [
                pt.strip()
                for pt in self.accepted_payment_types.split(",")
                if pt.strip()
            ]
        return []


class Shop(models.Model):
    """
    Represents a shop
    """

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    menu_image = models.ImageField(upload_to="shop_menus/", blank=True, null=True)
    category = models.CharField(
        max_length=50,
        choices=ShopCategoryEnum.choices,
        default=ShopCategoryEnum.RESTAURANT.value,
    )

    def __str__(self):
        return self.name


class GroupOrder(models.Model):
    """
    Represents a group order
    """

    name = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=GroupOrderStatusEnum.choices,
        default=GroupOrderStatusEnum.OPEN.value,
    )
    total_price = models.FloatField()
    delivery_fees = models.FloatField(default=0.0)
    vat = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="group_orders",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=6, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Represents a product in a shop
    """

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    price = models.FloatField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = ("shop", "name")


class GroupOrderItem(models.Model):
    """
    Represents an item in a group order
    """

    group_order = models.ForeignKey(
        GroupOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="group_order_items", null=True
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="group_order_items", null=True
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.FloatField()

    def __str__(self):
        return f"{self.name} (x{self.quantity}) - {self.price}"


class GroupOrderParticipant(models.Model):
    """
    Represents a participant in a group order
    """

    group_order = models.ForeignKey(
        GroupOrder, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="group_orders_participated"
    )
    amount = models.FloatField(default=0.0)
    paid_amount = models.FloatField(default=0.0)
    delivery_fees = models.FloatField(default=0.0)
    vat = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    payment_method = models.CharField(
        max_length=50, blank=True, null=True
    )  # e.g., "cash", "card", "instapay"
    payment_transaction_image = models.ImageField(
        upload_to="payment_transactions/", blank=True, null=True
    )

    @property
    def is_paid(self):
        return self.paid_amount == self.amount

    @property
    def partially_paid(self):
        return 0 < self.paid_amount < self.amount


class UserBalance(models.Model):
    """
    Represents a user's balance
    """

    creditor = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="creditor_balance"
    )
    debtor = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="debtor_debt"
    )
    amount = models.FloatField(default=0.0)

    def __str__(self):
        return f"User {self.user_id} - Balance: {self.balance}"
