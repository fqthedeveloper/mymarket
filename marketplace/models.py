from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    is_seller = models.BooleanField(default=False)

    # Seller details
    shop_name = models.CharField(max_length=200, blank=True, null=True)
    shop_address = models.TextField(blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 NEW: Default replies for buyer quick questions
    price_reply = models.CharField(max_length=300, blank=True, null=True)
    size_reply = models.CharField(max_length=300, blank=True, null=True)
    details_reply = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title


# ✅ FIXED SAVED MODEL (only change is saved_at added)
class SavedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user} saved {self.product}"


class Message(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver}"