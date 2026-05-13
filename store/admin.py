from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductReview,
    Wishlist,
    WishlistItem,
    Cart,
    CartItem,
    Coupon,
    Order,
    OrderItem
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'slug']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'price',
        'stock',
        'is_active',
        'is_featured'
    ]

    list_filter = [
        'category',
        'is_active',
        'is_featured'
    ]

    search_fields = ['name']

    list_editable = [
        'price',
        'stock',
        'is_active',
        'is_featured'
    ]

    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'user',
        'rating',
        'created_at'
    ]

    list_filter = [
        'rating',
        'created_at'
    ]

    search_fields = [
        'user__username',
        'comment'
    ]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'created_at'
    ]

    list_filter = ['created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number',
        'user',
        'total_amount',
        'status',
        'payment_status',
        'created_at'
    ]

    list_filter = [
        'status',
        'payment_status',
        'created_at'
    ]

    search_fields = [
        'order_number',
        'user__username'
    ]

    list_editable = ['status']


admin.site.register(Wishlist)
admin.site.register(WishlistItem)
admin.site.register(CartItem)
admin.site.register(Coupon)
admin.site.register(OrderItem)
