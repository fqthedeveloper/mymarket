from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import *


# ================= PROFILE =================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "is_seller",
        "is_verified",
        "shop_name",
        "qr_preview"
    )

    list_filter = (
        "is_seller",
        "is_verified"
    )

    search_fields = (
        "user__username",
        "shop_name"
    )

    list_editable = (
        "is_seller",
        "is_verified"
    )

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="40" height="40"/>',
                obj.qr_code.url
            )
        return "-"
    qr_preview.short_description = "QR"


# ================= PRODUCT =================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "image_preview",
        "title",
        "seller",
        "price",
        "stock",
        "created_at"
    )

    list_filter = (
        "seller",
        "created_at"
    )

    search_fields = (
        "title",
        "seller__username"
    )

    list_editable = (
        "price",
        "stock"
    )

    readonly_fields = (
        "created_at",
        "image_preview_large"
    )

    ordering = ("-created_at",)

    fieldsets = (

        ("Product Info", {
            "fields": (
                "title",
                "description",
                "seller",
                "image",
                "image_preview_large"
            )
        }),

        ("Pricing", {
            "fields": (
                "price",
                "stock"
            )
        }),

        ("Auto Replies", {
            "fields": (
                "price_reply",
                "size_reply",
                "details_reply"
            )
        }),

        ("Metadata", {
            "fields": (
                "created_at",
            )
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50"/>',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Image"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="200"/>',
                obj.image.url
            )
        return "-"


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

    ordering = ("-saved_at",)


# ================= CART =================

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "product",
        "quantity",
        "negotiated_price",
        "final_price_display",
        "discount_display",
        "total_price_display",
        "created_at"
    )

    search_fields = (
        "user__username",
        "product__title"
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    def final_price_display(self, obj):
        return obj.final_price()
    final_price_display.short_description = "Final Price"

    def discount_display(self, obj):
        return obj.discount()
    discount_display.short_description = "Discount"

    def total_price_display(self, obj):
        return obj.total_price()
    total_price_display.short_description = "Total"


# ================= CONVERSATION =================

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("timestamp",)


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

    inlines = [MessageInline]


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

    ordering = ("-timestamp",)

    def short_text(self, obj):
        return obj.text[:50]
    short_text.short_description = "Message"


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

    ordering = ("-last_seen",)


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

    actions = ["approve_orders", "reject_orders"]

    def approve_orders(self, request, queryset):
        queryset.update(status="approved")
    approve_orders.short_description = "Approve selected orders"

    def reject_orders(self, request, queryset):
        queryset.update(status="rejected")
    reject_orders.short_description = "Reject selected orders"


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
        "total_price",
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

    list_editable = (
        "status",
        "fraud_flag"
    )

    readonly_fields = (
        "created_at",
        "total_price"
    )

    actions = ["mark_shipped", "mark_delivered", "mark_fraud"]

    fieldsets = (

        ("Order Info", {
            "fields": (
                "product",
                "buyer",
                "seller",
                "price",
                "quantity",
                "total_price"
            )
        }),

        ("Payment", {
            "fields": (
                "payment_method",
            )
        }),

        ("Shipping Address", {
            "fields": (
                "address_line1",
                "address_line2",
                "city",
                "state",
                "pincode"
            )
        }),

        ("Status", {
            "fields": (
                "status",
                "fraud_flag",
                "created_at"
            )
        }),
    )

    def total_price(self, obj):
        return obj.total()

    def mark_shipped(self, request, queryset):
        queryset.update(status="shipped")
    mark_shipped.short_description = "Mark as Shipped"

    def mark_delivered(self, request, queryset):
        queryset.update(status="delivered")
    mark_delivered.short_description = "Mark as Delivered"

    def mark_fraud(self, request, queryset):
        queryset.update(fraud_flag=True)
    mark_fraud.short_description = "Mark as Fraud"


# ================= INVOICE =================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):

    list_display = (
        "invoice_number",
        "order",
        "pdf_preview",
        "created_at"
    )

    search_fields = (
        "invoice_number",
        "order__id"
    )

    readonly_fields = (
        "created_at",
    )

    def pdf_preview(self, obj):
        if obj.pdf:
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.pdf.url
            )
        return "-"