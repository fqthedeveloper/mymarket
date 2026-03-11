from django.contrib import admin
from .models import *


# ================= PROFILE =================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "is_seller",
        "is_verified",
        "shop_name"
    )

    list_filter = (
        "is_seller",
        "is_verified"
    )

    search_fields = (
        "user__username",
        "shop_name"
    )



# ================= PRODUCT =================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "seller",
        "price",
        "stock",
        "created_at"
    )

    list_filter = (
        "created_at",
        "seller"
    )

    search_fields = (
        "title",
        "seller__username"
    )

    readonly_fields = (
        "created_at",
    )



# ================= SAVED PRODUCTS =================

@admin.register(SavedProduct)
class SavedProductAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "product",
        "saved_at"
    )

    search_fields = (
        "user__username",
        "product__title"
    )

    list_filter = (
        "saved_at",
    )



# ================= CART =================

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "product",
        "quantity",
        "added_at",
        "total_price"
    )

    search_fields = (
        "user__username",
        "product__title"
    )

    list_filter = (
        "added_at",
    )



# ================= CONVERSATION =================

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "buyer",
        "seller",
        "created_at"
    )

    search_fields = (
        "product__title",
        "buyer__username",
        "seller__username"
    )

    list_filter = (
        "created_at",
    )



# ================= MESSAGE =================

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = (
        "sender",
        "conversation",
        "short_text",
        "timestamp",
        "delivered",
        "seen"
    )

    list_filter = (
        "delivered",
        "seen",
        "timestamp"
    )

    search_fields = (
        "sender__username",
        "text"
    )

    readonly_fields = (
        "timestamp",
    )

    def short_text(self, obj):
        return obj.text[:50]



# ================= USER STATUS =================

@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "is_online",
        "last_seen"
    )

    list_filter = (
        "is_online",
    )

    search_fields = (
        "user__username",
    )



# ================= ORDER REQUEST =================

@admin.register(OrderRequest)
class OrderRequestAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "buyer",
        "seller",
        "agreed_price",
        "status",
        "created_at"
    )

    list_filter = (
        "status",
        "created_at"
    )

    search_fields = (
        "product__title",
        "buyer__username",
        "seller__username"
    )



# ================= FINAL ORDER =================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "product",
        "buyer",
        "seller",
        "price",
        "quantity",
        "status",
        "payment_method",
        "fraud_flag",
        "created_at"
    )

    list_filter = (
        "status",
        "payment_method",
        "fraud_flag",
        "created_at"
    )

    search_fields = (
        "product__title",
        "buyer__username",
        "seller__username",
        "city",
        "pincode"
    )

    readonly_fields = (
        "created_at",
    )



# ================= INVOICE =================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):

    list_display = (
        "invoice_number",
        "order",
        "created_at"
    )

    search_fields = (
        "invoice_number",
        "order__id"
    )

    readonly_fields = (
        "created_at",
    )