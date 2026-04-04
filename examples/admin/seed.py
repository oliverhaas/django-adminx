#!/usr/bin/env python
"""Seed the database with example data."""

import os
import sys
from decimal import Decimal
from pathlib import Path

# Add the example project to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import django

django.setup()

from django.contrib.auth.models import User
from shop.models import Category, Customer, Order, OrderItem, Product, Tag

# Superuser
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin")
    print("Created superuser: admin / admin")

# Tags
tag_names = ["organic", "sale", "new", "bestseller", "limited", "seasonal", "vegan", "imported"]
tags = {name: Tag.objects.get_or_create(name=name)[0] for name in tag_names}

# Categories
categories_data = [
    ("Coffee", "coffee", "Single origin and blends"),
    ("Tea", "tea", "Loose leaf and bagged teas"),
    ("Equipment", "equipment", "Brewing and grinding equipment"),
    ("Accessories", "accessories", "Cups, filters, and more"),
]
categories = {}
for i, (name, slug, desc) in enumerate(categories_data):
    cat, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name, "description": desc, "sort_order": i})
    categories[slug] = cat

# Products
products_data = [
    ("Ethiopian Yirgacheffe", "eth-yirg", "coffee", "29.90", "18.50", 42, "active", True, ["organic", "bestseller"]),
    ("Colombian Supremo", "col-sup", "coffee", "24.90", "15.00", 78, "active", False, ["organic"]),
    ("Sumatra Mandheling", "sum-mand", "coffee", "27.50", "17.00", 35, "active", False, ["imported"]),
    ("Kenya AA", "ken-aa", "coffee", "31.00", "20.00", 15, "active", True, ["new", "limited"]),
    ("Guatemala Antigua", "gua-ant", "coffee", "26.00", "16.00", 0, "archived", False, ["organic"]),
    ("Brazil Santos", "bra-san", "coffee", "19.90", "11.00", 120, "active", False, ["sale"]),
    ("House Blend", "house-blend", "coffee", "18.50", "10.00", 200, "active", True, ["bestseller"]),
    ("Decaf Colombian", "decaf-col", "coffee", "22.90", "14.00", 55, "active", False, []),
    ("Earl Grey Supreme", "earl-grey", "tea", "14.90", "6.50", 90, "active", False, ["bestseller"]),
    ("Sencha Green", "sencha", "tea", "16.50", "7.00", 60, "active", False, ["organic", "imported"]),
    ("English Breakfast", "eng-break", "tea", "12.90", "5.50", 110, "active", False, []),
    ("Chamomile Dream", "chamomile", "tea", "11.50", "4.50", 45, "active", False, ["organic", "vegan"]),
    ("Rooibos Vanilla", "rooibos", "tea", "13.90", "6.00", 30, "draft", False, ["new"]),
    ("V60 Dripper", "v60", "equipment", "32.00", "18.00", 25, "active", True, ["bestseller"]),
    ("Chemex 6-Cup", "chemex-6", "equipment", "45.00", "28.00", 12, "active", False, []),
    ("Hario Hand Grinder", "hario-grind", "equipment", "55.00", "32.00", 8, "active", False, ["new"]),
    ("French Press 1L", "french-1l", "equipment", "28.00", "14.00", 40, "active", False, ["sale"]),
    ("Gooseneck Kettle", "gooseneck", "equipment", "65.00", "38.00", 6, "draft", False, []),
    ("Paper Filters (100pk)", "filters-100", "accessories", "8.90", "3.00", 300, "active", False, []),
    ("Ceramic Mug 350ml", "mug-350", "accessories", "14.00", "5.50", 80, "active", False, ["seasonal"]),
    ("Travel Tumbler", "tumbler", "accessories", "22.00", "11.00", 35, "active", True, ["new", "bestseller"]),
    ("Coffee Scale", "scale", "accessories", "38.00", "20.00", 15, "active", False, []),
]

products = {}
for name, sku, cat_slug, price, cost, stock, status, featured, tag_list in products_data:
    product, created = Product.objects.get_or_create(
        sku=sku,
        defaults={
            "name": name,
            "slug": sku,
            "category": categories[cat_slug],
            "price": Decimal(price),
            "cost": Decimal(cost),
            "stock": stock,
            "status": status,
            "is_featured": featured,
        },
    )
    if created and tag_list:
        product.tags.set([tags[t] for t in tag_list])
    products[sku] = product

# Customers
customers_data = [
    ("alice@example.com", "Alice", "Johnson", "+1-555-0101"),
    ("bob@example.com", "Bob", "Smith", "+1-555-0102"),
    ("carol@example.com", "Carol", "Williams", ""),
    ("dave@example.com", "Dave", "Brown", "+1-555-0104"),
    ("eve@example.com", "Eve", "Davis", "+1-555-0105"),
]
customers = {}
for email, first, last, phone in customers_data:
    customer, _ = Customer.objects.get_or_create(
        email=email,
        defaults={"first_name": first, "last_name": last, "phone": phone},
    )
    customers[email] = customer

# Orders
orders_data = [
    ("alice@example.com", "delivered", [("eth-yirg", 2, "29.90"), ("filters-100", 1, "8.90")]),
    ("alice@example.com", "shipped", [("earl-grey", 3, "14.90"), ("mug-350", 2, "14.00")]),
    ("bob@example.com", "confirmed", [("house-blend", 1, "18.50"), ("v60", 1, "32.00")]),
    ("bob@example.com", "pending", [("ken-aa", 1, "31.00")]),
    ("carol@example.com", "delivered", [("chemex-6", 1, "45.00"), ("col-sup", 3, "24.90")]),
    ("dave@example.com", "shipped", [("tumbler", 1, "22.00"), ("sencha", 2, "16.50")]),
    ("eve@example.com", "pending", [("hario-grind", 1, "55.00"), ("bra-san", 2, "19.90"), ("filters-100", 2, "8.90")]),
    ("alice@example.com", "cancelled", [("french-1l", 1, "28.00")]),
]

for email, status, items in orders_data:
    order = Order.objects.create(customer=customers[email], status=status)
    for sku, qty, price in items:
        OrderItem.objects.create(order=order, product=products[sku], quantity=qty, unit_price=Decimal(price))

print(
    f"Seeded: {Product.objects.count()} products, {Customer.objects.count()} customers, {Order.objects.count()} orders",
)
