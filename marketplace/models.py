from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)

    is_seller = models.BooleanField(default=False)

    is_verified = models.BooleanField(default=False)   # ⭐ NEW

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

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

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
    

class Cart(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def total_price(self):
        return self.product.price * self.quantity

# ================= CHAT ROOM =================

class Conversation(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buyer_chats"
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="seller_chats"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} - {self.buyer}"


# ================= MESSAGE =================

class Message(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE
    )

    sender = models.ForeignKey(User,on_delete=models.CASCADE)

    text = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    delivered = models.BooleanField(default=False)

    seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} : {self.text}"
    

class UserStatus(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    is_online = models.BooleanField(default=False)

    last_seen = models.DateTimeField(auto_now=True)

# ================= ORDER REQUEST =================

class OrderRequest(models.Model):

    STATUS = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_orders")

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_orders")

    agreed_price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} - {self.agreed_price}"
    
# ================= FINAL ORDER =================

class Order(models.Model):

    STATUS = (
        ("pending","Pending"),
        ("approved","Approved"),
        ("rejected","Rejected"),
        ("shipped","Shipped"),
        ("delivered","Delivered"),
    )

    PAYMENT = (
        ("cod","Cash On Delivery"),
        ("upi","UPI"),
        ("card","Card"),
        ("bank","Bank Transfer"),
    )

    product = models.ForeignKey(Product,on_delete=models.CASCADE)

    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sales"
    )

    price = models.DecimalField(max_digits=10,decimal_places=2)

    quantity = models.PositiveIntegerField(default=1)

    status = models.CharField(max_length=20,choices=STATUS,default="pending")

    payment_method = models.CharField(max_length=20,choices=PAYMENT)

    # SHIPPING ADDRESS
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200,blank=True,null=True)

    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)

    fraud_flag = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"Order {self.id} - {self.product}"


# ================= INVOICE =================

class Invoice(models.Model):

    order = models.OneToOneField(Order,on_delete=models.CASCADE)

    invoice_number = models.CharField(max_length=100)

    pdf = models.FileField(upload_to="invoices/",blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number