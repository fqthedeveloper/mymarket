from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Product, Profile, Message, SavedProduct
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from .forms import RegisterForm
from .models import Profile

# ================= HOME PAGE =================

def home(request):

    search_query = request.GET.get("q", "")

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


    if request.user.is_authenticated:

        user_messages = Message.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).values_list("product_id", flat=True)

        saved_products = SavedProduct.objects.filter(
            user=request.user
        ).values_list("product_id", flat=True)

        for product in products:

            product.has_messages = product.id in user_messages
            product.is_saved = product.id in saved_products

    else:

        for product in products:
            product.has_messages = False
            product.is_saved = False


    return render(request, "home.html", {
        "products": products
    })


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


@login_required
def toggle_wishlist(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    saved = SavedProduct.objects.filter(
        user=request.user,
        product=product
    )

    if saved.exists():
        saved.delete()   # remove from wishlist
    else:
        SavedProduct.objects.create(
            user=request.user,
            product=product
        )

    return redirect(request.META.get("HTTP_REFERER", "/"))


# ================= REGISTER =================
def register(request):

    success = False

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists")

            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered")

            else:

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )

                user.first_name = first_name
                user.last_name = last_name
                user.is_active = False
                user.save()

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                domain = get_current_site(request).domain

                verification_link = f"http://{domain}/verify/{uid}/{token}/"

                try:

                    send_mail(
                        "Verify your account",
                        f"Click the link below to verify your account:\n\n{verification_link}",
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                    )

                    success = True

                except Exception:

                    messages.error(
                        request,
                        "Account created but email verification could not be sent."
                    )

        else:
            messages.error(request, "Please correct the form errors.")

    else:
        form = RegisterForm()

    return render(request, "register.html", {
        "form": form,
        "success": success
    })


def verify_email(request, uidb64, token):

    try:

        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

    except:

        user = None

    if user and default_token_generator.check_token(user, token):

        user.is_active = True
        user.save()

        login(request, user)

        return redirect("login_success")

    return render(request, "verification_failed.html")


# ================= LOGIN REDIRECT =================

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            if not user.is_active:
                messages.error(request, "Please verify your email before login.")
                return redirect("login")

            login(request, user)

            messages.success(request, "Login successful!")

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect("login_success")

        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")

@login_required
def login_success(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    next_url = request.GET.get("next")

    if next_url:
        return redirect(next_url)

    if profile.is_seller:
        return redirect("seller_dashboard")

    return redirect("home")


# ================= SELLER DASHBOARD =================
@login_required
def seller_dashboard(request):

    profile, created = Profile.objects.get_or_create(user=request.user)

    if not profile.is_seller:
        return redirect("home")

    products = Product.objects.filter(seller=request.user).order_by("-id")

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


@login_required
def upload_product(request):

    profile, created = Profile.objects.get_or_create(user=request.user)

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


@login_required
def edit_product(request, product_id):

    product = get_object_or_404(Product, id=product_id, seller=request.user)

    if request.method == "POST":

        product.title = request.POST.get("title")
        product.description = request.POST.get("description")

        if request.FILES.get("image"):
            product.image = request.FILES.get("image")

        product.price_reply = request.POST.get("price_reply")
        product.size_reply = request.POST.get("size_reply")
        product.details_reply = request.POST.get("details_reply")

        product.save()

        return redirect("seller_dashboard")

    return render(request, "edit_product.html", {
        "product": product
    })


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
def profile_settings(request):

    user = request.user
    profile = user.profile

    if request.method == "POST":

        # USER BASIC INFO
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")

        if first_name:
            user.first_name = first_name

        if last_name:
            user.last_name = last_name

        if username:
            user.username = username

        if email:
            user.email = email

        user.save()

        # SELLER EXTRA INFO
        if profile.is_seller:

            shop_name = request.POST.get("shop_name")
            shop_address = request.POST.get("shop_address")

            if shop_name:
                profile.shop_name = shop_name

            if shop_address:
                profile.shop_address = shop_address

            if request.FILES.get("qr_code"):
                profile.qr_code = request.FILES.get("qr_code")

        profile.save()

        messages.success(request, "Profile updated successfully")

        return redirect("profile_settings")

    return render(request, "profile_settings.html", {
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


@login_required
def seller_settings(request):

    user = request.user
    profile = user.profile

    if not profile.is_seller:
        return redirect("home")

    if request.method == "POST":

        # USER INFO
        username = request.POST.get("username")
        email = request.POST.get("email")

        if username:
            user.username = username

        if email:
            user.email = email

        user.save()

        # SHOP INFO
        profile.shop_name = request.POST.get("shop_name")
        profile.shop_address = request.POST.get("shop_address")

        if request.FILES.get("qr_code"):
            profile.qr_code = request.FILES.get("qr_code")

        profile.save()

        messages.success(request, "Seller settings updated successfully")

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