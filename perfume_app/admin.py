# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Count
from .models import ( Category, Product, ProductImage, Review, Cart, CartItem, Wishlist, Order, OrderItem, NewsletterSubscriber, SiteSettings, User, Contact)
from django.contrib.auth.admin import UserAdmin

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Product Count'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "-"
    preview_image.short_description = 'Preview'

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'title', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'price', 'size', 'stock',
        'is_active', 'is_featured', 'is_best_seller', 'average_rating'
    )
    list_filter = (
        'category', 'is_active', 'is_featured', 'is_best_seller',
        'gender', 'size', 'created_at'
    )
    search_fields = ('name', 'description', 'sku', 'fragrance_notes')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = (
        'sku', 'created_at', 'updated_at', 'average_rating',
        'review_count', 'discount_percentage', 'cost_per_ml'
    )
    inlines = [ProductImageInline, ReviewInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': (
                'price', 'compare_price', 'sku', 'stock',
                'low_stock_threshold', 'cost_per_ml'
            )
        }),
        ('Product Details', {
            'fields': (
                'size', 'gender', 'fragrance_notes',
                'intensity', 'longevity'
            )
        }),
        ('Flags', {
            'fields': (
                'is_active', 'is_featured', 'is_best_seller',
                'is_new', 'discount_percentage'
            )
        }),
        ('Ratings & Reviews', {
            'fields': ('average_rating', 'review_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def average_rating(self, obj):
        return obj.average_rating()
    average_rating.short_description = 'Avg Rating'

    def review_count(self, obj):
        return obj.review_count()
    review_count.short_description = 'Review Count'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_active', 'verified_purchase', 'created_at')
    list_filter = ('rating', 'is_active', 'verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'total_price')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'subtotal', 'total')
    readonly_fields = ('user', 'total_items', 'subtotal', 'total')
    inlines = [CartItemInline]

    def has_add_permission(self, request):
        return False


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_count', 'created_at')
    readonly_fields = ('user', 'product_count', 'created_at', 'updated_at')
    filter_horizontal = ('products',)

    def has_add_permission(self, request):
        return False

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'first_name', 'last_name',
        'total', 'status', 'payment_status', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username', 'first_name', 'last_name', 'email')
    readonly_fields = (
        'order_number', 'user', 'email', 'phone', 'first_name', 'last_name',
        'address', 'city', 'state', 'zip_code', 'country',
        'subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total',
        'created_at', 'updated_at'
    )
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Customer Information', {
            'fields': (
                'email', 'phone', 'first_name', 'last_name',
                'address', 'city', 'state', 'zip_code', 'country'
            )
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_method')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'tax_amount', 'shipping_cost',
                'discount_amount', 'total'
            )
        }),
        ('Shipping & Tracking', {
            'fields': ('tracking_number', 'shipped_date', 'delivered_date'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Allow status changes but keep other fields readonly
        if obj:
            return [f for f in self.readonly_fields if f != 'status']
        return self.readonly_fields

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('token', 'created_at', 'updated_at')

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Allow only one instance
        return not SiteSettings.objects.exists()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'newsletter_subscribed')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'date_of_birth', 'newsletter_subscribed')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'date_of_birth', 'newsletter_subscribed')
        }),
    )

# Register other models

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')   # show in list view
    list_filter = ('subject', 'created_at')                     # filters in sidebar
    search_fields = ('name', 'email', 'subject', 'message')     # search box
    readonly_fields = ('created_at',)
