from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "testapp"
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200)
    slug = models.SlugField(default="", blank=True)
    body = models.TextField(default="", blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    publish_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "testapp"

    def __str__(self) -> str:
        return self.title
