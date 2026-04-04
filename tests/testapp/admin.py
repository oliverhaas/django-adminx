import django_adminx as admin

from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "is_featured", "priority", "publish_date", "created_at"]
    list_display_links = ["title"]
    list_editable = ["status", "is_featured", "priority"]
    list_filter = ["status", "is_featured", "category"]
    search_fields = ["title", "slug", "body"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["category"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at"]
    list_only_fields = ["id", "title", "category_id", "status", "is_featured", "priority", "publish_date", "created_at"]
    fieldsets = [
        (None, {"fields": ["title", "slug", "body", "category"]}),
        ("Publishing", {"fields": ["status", "is_featured", "priority", "publish_date"]}),
        ("Metadata", {"fields": ["created_at"], "classes": ["collapse"]}),
    ]
