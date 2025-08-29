from django.contrib.auth import get_user_model
from django.db import models

# DEMO

User = get_user_model()


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_supplier"

    def __str__(self):
        return self.name


class Category(models.Model):
    title = models.CharField(max_length=200)

    class Meta:
        db_table = "core_category"

    def __str__(self):
        return self.title


class Item(models.Model):
    name = models.CharField(max_length=200)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="items", null=True)
    categories = models.ManyToManyField(Category, related_name="items")  # авто-M2M таблица
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_item"

    def __str__(self):
        return self.name


class Tag(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        db_table = "core_tag"

    def __str__(self):
        return self.title


class ItemTag(models.Model):
    """M2M через кастомный through с доп. полями"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    weight = models.IntegerField(default=0)

    class Meta:
        db_table = "core_item_tag"
        unique_together = (("item", "tag"),)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, default="")

    class Meta:
        db_table = "core_profile"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_order"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "core_order_item"
        unique_together = (("order", "item"),)
