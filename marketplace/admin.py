from django.contrib import admin
from .models import Product, Message, Profile

admin.site.register(Product)
admin.site.register(Message)
admin.site.register(Profile)