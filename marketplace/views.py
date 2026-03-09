from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Product, Profile, Message, SavedProduct


# ================= HOME PAGE =================
def home(request):

    search_query = request.GET.get("q")

    products = Product.objects.all().order_by("-created_at")

    # SEARCH REORDER LOGIC
    if search_query:
        matched = []
        others = []

        for product in products:
            text = (product.title + " " + product.description).lower()

            if search_query.lower() in text:
                matched.append(product)
            else:
                others.append(product)

        products = matched + others


    for product in products:
        if request.user.is_authenticated:
            product.has_messages = Message.objects.filter(
                product=product
            ).filter(
                Q(sender=request.user) | Q(receiver=request.user)
            ).exists()

            product.is_saved = SavedProduct.objects.filter(
                user=request.user,
                product=product
            ).exists()
        else:
            product.has_messages = False
            product.is_saved = False

    return render(request, "home.html", {"products": products})


# ================= WISHLIST PAGE =================
@login_required
def wishlist(request):
    saved_items = SavedProduct.objects.filter(user=request.user).select_related("product")
    products = [item.product for item in saved_items]

    for product in products:
        product.has_messages = Message.objects.filter(
            product=product
        ).filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).exists()

        product.is_saved = True

    return render(request, "home.html", {"products": products})


# ================= REGISTER =================
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect("login_success")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


# ================= LOGIN REDIRECT =================
@login_required
def login_success(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)

    if profile.is_seller:
        return redirect("seller_dashboard")

    return redirect("home")


# ================= SELLER DASHBOARD =================
@login_required
def seller_dashboard(request):
    profile = Profile.objects.get(user=request.user)

    if not profile.is_seller:
        return redirect("home")

    products = Product.objects.filter(seller=request.user)

    for product in products:

        buyer_ids = Message.objects.filter(
            product=product
        ).exclude(
            sender=request.user
        ).values_list("sender", flat=True).distinct()

        product.chat_buyers = User.objects.filter(id__in=buyer_ids)

        product.chat_count = product.chat_buyers.count()

        product.has_messages = product.chat_count > 0

    return render(request, "seller_dashboard.html", {
        "products": products
    })


# ================= UPLOAD PRODUCT =================
@login_required
def upload_product(request):
    profile = Profile.objects.get(user=request.user)

    if not profile.is_seller:
        return redirect("home")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        price_reply = request.POST.get("price_reply")
        size_reply = request.POST.get("size_reply")
        details_reply = request.POST.get("details_reply")

        if title and description and image:
            Product.objects.create(
                seller=request.user,
                title=title,
                description=description,
                image=image,
                price_reply=price_reply,
                size_reply=size_reply,
                details_reply=details_reply
            )
            return redirect("seller_dashboard")

    return render(request, "upload.html")


# ================= DELETE PRODUCT =================
@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    product.delete()
    return redirect("seller_dashboard")


# ================= CHAT =================
@login_required
def chat_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user == product.seller:

        buyer_username = request.GET.get("buyer")

        if buyer_username:
            buyer = get_object_or_404(User, username=buyer_username)

            messages = Message.objects.filter(
                product=product
            ).filter(
                Q(sender=buyer, receiver=request.user) |
                Q(sender=request.user, receiver=buyer)
            ).order_by("timestamp")

        else:
            messages = Message.objects.none()

    else:

        messages = Message.objects.filter(
            product=product
        ).filter(
            Q(sender=request.user, receiver=product.seller) |
            Q(sender=product.seller, receiver=request.user)
        ).order_by("timestamp")

    return render(request, "chat.html", {
        "product": product,
        "messages": messages
    })


# ================= SEND MESSAGE =================
@login_required
def send_message(request):
    if request.method == "POST":

        product_id = request.POST.get("product_id")
        content = request.POST.get("content")
        buyer_username = request.POST.get("buyer")

        product = get_object_or_404(Product, id=product_id)

        if request.user == product.seller:

            buyer = get_object_or_404(User, username=buyer_username)
            receiver = buyer

            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                product=product,
                text=content
            )

            return redirect(f"/chat/{product.id}/?buyer={receiver.username}")

        else:

            receiver = product.seller

            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                product=product,
                text=content
            )

            if content == "What is the price?" and product.price_reply:
                Message.objects.create(
                    sender=product.seller,
                    receiver=request.user,
                    product=product,
                    text=product.price_reply
                )

            if content == "What sizes are available?" and product.size_reply:
                Message.objects.create(
                    sender=product.seller,
                    receiver=request.user,
                    product=product,
                    text=product.size_reply
                )

            if content == "Can you share more details about this product?" and product.details_reply:
                Message.objects.create(
                    sender=product.seller,
                    receiver=request.user,
                    product=product,
                    text=product.details_reply
                )

            return redirect("chat", product_id=product.id)

    return redirect("home")


# ================= SELLER SETTINGS =================
@login_required
def seller_settings(request):
    profile = request.user.profile

    if not profile.is_seller:
        return redirect("home")

    if request.method == "POST":
        profile.shop_name = request.POST.get("shop_name")
        profile.shop_address = request.POST.get("shop_address")

        if request.FILES.get("qr_code"):
            profile.qr_code = request.FILES.get("qr_code")

        profile.save()
        return redirect("seller_settings")

    return render(request, "seller_settings.html", {
        "profile": profile
    })


# ================= SELLER PROFILE PAGE =================
def seller_profile(request, username):
    seller = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=seller)

    products = Product.objects.filter(seller=seller).order_by("-created_at")

    return render(request, "seller_profile.html", {
        "seller": seller,
        "profile": profile,
        "products": products
    })


# ================= SAVE / UNSAVE PRODUCT =================
@login_required
def toggle_save(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    saved = SavedProduct.objects.filter(
        user=request.user,
        product=product
    )

    if saved.exists():
        saved.delete()
    else:
        SavedProduct.objects.create(
            user=request.user,
            product=product
        )

    return redirect("home")