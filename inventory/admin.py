from django.contrib import admin

from .models import Category, Item, Sale


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color", "created_at")
    list_filter = ("color",)
    search_fields = ("name", "user__username")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "category",
        "status",
        "cost_cents",
        "acquired_on",
    )
    list_filter = ("status", "condition", "category")
    search_fields = ("name", "notes", "user__username")
    date_hierarchy = "acquired_on"


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("item", "price_cents", "fees_cents", "channel", "sold_on")
    list_filter = ("channel",)
    search_fields = ("item__name", "item__user__username")
    date_hierarchy = "sold_on"
