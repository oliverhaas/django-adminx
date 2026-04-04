from django.contrib import admin

from django_adminx import BaseModelAdmin

from .models import Category, Customer, Order, OrderItem, Product, ProductImage, Tag

# --- Inlines ---


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["url", "alt_text", "is_primary", "sort_order"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ["product", "quantity", "unit_price"]
    raw_id_fields = ["product"]


# --- ModelAdmins ---


@admin.register(Category)
class CategoryAdmin(BaseModelAdmin):
    list_display = ["name", "slug", "sort_order"]
    list_editable = ["sort_order"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(BaseModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(BaseModelAdmin):
    list_display = ["name", "sku", "category", "price", "stock", "status", "is_featured", "created_at"]
    list_only_fields = ["id", "name", "sku", "category_id", "price", "stock", "status", "is_featured", "created_at"]
    list_filter = ["status", "is_featured", "category", "tags"]
    list_editable = ["status", "is_featured"]
    search_fields = ["name", "sku", "description"]
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ["category"]
    filter_horizontal = ["tags"]
    date_hierarchy = "created_at"
    inlines = [ProductImageInline]
    fieldsets = [
        (None, {"fields": ["name", "slug", "description", "category", "tags"]}),
        ("Pricing & Stock", {"fields": ["price", "cost", "sku", "stock"]}),
        ("Status", {"fields": ["status", "is_featured"]}),
    ]


@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    list_display = ["email", "first_name", "last_name", "phone", "created_at"]
    list_only_fields = ["id", "email", "first_name", "last_name", "phone", "created_at"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["created_at"]


@admin.register(Order)
class OrderAdmin(BaseModelAdmin):
    list_display = ["__str__", "customer", "status", "created_at"]
    list_only_fields = ["id", "customer_id", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["customer__email", "customer__last_name"]
    raw_id_fields = ["customer"]
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    readonly_fields = ["created_at", "updated_at"]
