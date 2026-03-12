from django.utils.timezone import localtime
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.db.models import Q, Max
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
from .models import Profile, Product, Message, SavedProduct, Cart, Conversation, UserStatus, OrderRequest, Order, Invoice

# ================= HOME PAGE =================

def home(request):

    search_query = request.GET.get("q", "")

    products = Product.objects.all().order_by("-created_at")


    # ================= SEARCH =================
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


    # ================= USER FEATURES =================
    if request.user.is_authenticated:


        # conversations where user involved
        conversations = Conversation.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user)
        )


        # products where chat exists
        user_products = conversations.values_list(
            "product_id", flat=True
        )


        saved_products = SavedProduct.objects.filter(
            user=request.user
        ).values_list("product_id", flat=True)


        for product in products:

            product.has_messages = product.id in user_products

            product.is_saved = product.id in saved_products


    else:

        for product in products:

            product.has_messages = False
            product.is_saved = False


    return render(request, "home.html", {
        "products": products,
        "page_title": "Home"
    })


# ================= Aboutus =================
def about(request):
    return render(request, "about.html")

# ================= WISHLIST PAGE =================
@login_required
def wishlist(request):

    saved_items = SavedProduct.objects.filter(
        user=request.user
    ).select_related("product", "product__seller")

    products = []

    for item in saved_items:

        product = item.product

        # check messages via conversation
        product.has_messages = Message.objects.filter(
            conversation__product=product
        ).filter(
            Q(sender=request.user) |
            Q(conversation__buyer=request.user) |
            Q(conversation__seller=request.user)
        ).exists()

        product.is_saved = True

        products.append(product)

    return render(request, "home.html", {
        "products": products,
        "page_title": "Wishlist"
    })


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
                        "Exatica: Ecommerce Account Verification",
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

    # ================= BLOCK LOGIN PAGE IF USER ALREADY LOGGED IN =================

    if request.user.is_authenticated:

        profile, created = Profile.objects.get_or_create(
            user=request.user
        )

        if profile.is_seller:
            return redirect("seller_dashboard")

        return redirect("home")


    # ================= LOGIN PROCESS =================

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if not user.is_active:

                messages.error(
                    request,
                    "Please verify your email before login."
                )

                return render(request, "login.html")

            login(request, user)

            messages.success(request, "Login successful!")

            next_url = request.GET.get("next")

            if next_url:
                return redirect(next_url)

            return redirect("login_success")

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

            return render(request, "login.html")


    return render(request, "login.html")


# ================= LOGIN SUCCESS REDIRECT =================

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

    products = Product.objects.filter(
        seller=request.user
    ).order_by("-id")

    total_chat_count = 0

    for product in products:

        conversations = Conversation.objects.filter(
            product=product,
            seller=request.user
        )

        buyer_ids = conversations.values_list(
            "buyer_id", flat=True
        ).distinct()

        product.chat_buyers = User.objects.filter(
            id__in=buyer_ids
        )

        product.chat_count = product.chat_buyers.count()

        product.has_messages = product.chat_count > 0

        total_chat_count += product.chat_count

    return render(request, "seller_dashboard.html", {
        "products": products,
        "chat_count": total_chat_count
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

        price = request.POST.get("price")
        stock = request.POST.get("stock")

        price_reply = request.POST.get("price_reply")
        size_reply = request.POST.get("size_reply")
        details_reply = request.POST.get("details_reply")

        if title and description and image:

            Product.objects.create(
                seller=request.user,
                title=title,
                description=description,
                image=image,
                price=price,
                stock=stock,
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

        product.price = request.POST.get("price")
        product.stock = request.POST.get("stock")

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

# ================= START CHAT =================

@login_required
def start_chat(request,product_id):

    product=get_object_or_404(Product,id=product_id)

    conversation,created=Conversation.objects.get_or_create(
        product=product,
        buyer=request.user,
        seller=product.seller
    )

    return redirect("chat_room",conversation.id)


@login_required
def chat_room(request,conversation_id):

    conversation=get_object_or_404(Conversation,id=conversation_id)

    messages=Message.objects.filter(
        conversation=conversation
    ).order_by("timestamp")

    Message.objects.filter(
        conversation=conversation
    ).exclude(sender=request.user).update(seen=True)

    return render(request,"chat_room.html",{
        "conversation":conversation,
        "messages":messages
    })


@login_required
def send_message(request):

    if request.method=="POST":

        conversation_id=request.POST["conversation_id"]
        text=request.POST["text"]

        conversation=Conversation.objects.get(id=conversation_id)

        msg=Message.objects.create(
            conversation=conversation,
            sender=request.user,
            text=text,
            delivered=True
        )

        return JsonResponse({"status":"ok"})


@login_required
def fetch_messages(request, conversation_id):

    conversation = Conversation.objects.get(id=conversation_id)

    messages = Message.objects.filter(
        conversation=conversation
    ).order_by("timestamp")

    data = []

    for m in messages:

        if m.timestamp:
            time_value = localtime(m.timestamp).strftime("%I:%M %p")
        else:
            time_value = ""

        data.append({
            "text": m.text,
            "mine": m.sender == request.user,
            "time": time_value,
            "delivered": m.delivered,
            "seen": m.seen
        })

    return JsonResponse({"messages": data})


@login_required
def typing_status(request):

    conversation=request.GET.get("conversation")

    user=request.user.username

    return JsonResponse({"typing":user})


@login_required
def user_status(request,user_id):

    status=UserStatus.objects.get(user_id=user_id)

    return JsonResponse({

        "online":status.is_online,

        "last_seen":localtime(status.last_seen).strftime("%I:%M %p")

    })

# ================= SELLER CHATS =================

@login_required
def seller_chats(request):

    conversations = Conversation.objects.filter(
        seller=request.user
    )

    # Order by latest message
    conversations = conversations.annotate(
        last_message=Max("message__timestamp")
    ).order_by("-last_message")

    unread = {}

    for c in conversations:

        unread[c.id] = Message.objects.filter(
            conversation=c,
            seen=False
        ).exclude(sender=request.user).count()

    return render(request,"seller_chats.html",{
        "conversations":conversations,
        "unread":unread
    })


# ================= BUYER CHATS =================

@login_required
def buyer_chats(request):

    conversations = Conversation.objects.filter(
        buyer=request.user
    )

    conversations = conversations.annotate(
        last_message=Max("message__timestamp")
    ).order_by("-last_message")

    unread = {}

    for c in conversations:

        unread[c.id] = Message.objects.filter(
            conversation=c,
            seen=False
        ).exclude(sender=request.user).count()

    return render(request,"buyer_chats.html",{
        "conversations":conversations,
        "unread":unread
    })

# ================= ADMIN MONITOR =================

@login_required
def admin_chats(request):

    if not request.user.is_superuser:
        return redirect("home")

    conversations=Conversation.objects.all()

    return render(request,"admin_chats.html",{
        "conversations":conversations
    })
    
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

def product_detail(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    seller_profile = Profile.objects.get(user=product.seller)

    return render(request, "product_detail.html", {
        "product": product,
        "seller_profile": seller_profile
    })
    
    
@login_required
def add_to_cart(request,product_id):

    product = get_object_or_404(Product,id=product_id)

    cart_item,created = Cart.objects.get_or_create(

        user=request.user,
        product=product,

        defaults={
            "quantity":1,
            "negotiated_price":None
        }

    )

    if not created:

        cart_item.quantity += 1
        cart_item.negotiated_price = None
        cart_item.save()

    return redirect("cart")

@login_required
def add_negotiated_to_cart(request,product_id,price):

    product = get_object_or_404(Product,id=product_id)

    cart_item,created = Cart.objects.get_or_create(

        user=request.user,
        product=product

    )

    cart_item.negotiated_price = price
    cart_item.quantity = 1
    cart_item.save()

    return redirect("cart")


@login_required
def cart_view(request):

    cart_items = Cart.objects.filter(user=request.user)

    total = 0

    for item in cart_items:
        total += item.total_price()

    return render(request,"cart.html",{

        "cart_items":cart_items,
        "total":total

    })


@login_required
def update_cart_quantity(request):

    cart_id = request.POST.get("cart_id")
    action = request.POST.get("action")

    cart = get_object_or_404(Cart,id=cart_id,user=request.user)

    if action == "plus":
        cart.quantity += 1

    elif action == "minus":
        if cart.quantity > 1:
            cart.quantity -= 1

    cart.save()

    item_total = cart.total_price()

    cart_items = Cart.objects.filter(user=request.user)

    cart_total = 0

    for item in cart_items:
        cart_total += item.total_price()

    return JsonResponse({

        "quantity":cart.quantity,
        "item_total":item_total,
        "cart_total":cart_total

    })


@login_required
def remove_cart(request,cart_id):

    cart_item = get_object_or_404(Cart,id=cart_id,user=request.user)

    cart_item.delete()

    return redirect("cart")

@login_required
def negotiation_order(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    # find conversation
    conversation = Conversation.objects.filter(
        product=product,
        seller=request.user
    ).first()

    if not conversation:
        return redirect("seller_dashboard")

    buyer = conversation.buyer

    if request.method == "POST":

        price = request.POST.get("price")

        if not price:
            return redirect("chat_room", conversation.id)

        # ADD PRODUCT DIRECTLY TO BUYER CART
        cart_item, created = Cart.objects.get_or_create(

            user=buyer,
            product=product,

            defaults={
                "quantity": 1,
                "negotiated_price": price
            }
        )

        if not created:
            cart_item.negotiated_price = price
            cart_item.quantity = 1
            cart_item.save()

    return redirect("seller_dashboard")

@login_required
def cart_plus(request,cart_id):

    cart = get_object_or_404(Cart,id=cart_id,user=request.user)

    cart.quantity += 1
    cart.save()

    return redirect("cart")


@login_required
def cart_minus(request,cart_id):

    cart = get_object_or_404(Cart,id=cart_id,user=request.user)

    if cart.quantity > 1:
        cart.quantity -= 1
        cart.save()

    return redirect("cart")


@login_required
def generate_invoice(request,order_id):

    order = get_object_or_404(Order,id=order_id)

    invoice = Invoice.objects.create(

        order=order,

        invoice_number=f"INV-{order.id}"
    )

    send_mail(

        "Invoice Generated",

        f"""
Invoice: {invoice.invoice_number}

Product: {order.product.title}

Quantity: {order.quantity}

Total: ₹{order.total()}
        """,

        settings.EMAIL_HOST_USER,

        [order.buyer.email,order.seller.email],

        fail_silently=True
    )

    return redirect("home")


@login_required
def place_order(request):

    if request.method == "POST":

        if not request.POST.get("terms"):
            return redirect("cart")

        return redirect("checkout")

    return redirect("cart")
    

@login_required
def checkout(request):

    cart_items = Cart.objects.filter(user=request.user)

    total = 0

    for item in cart_items:
        total += item.total_price()

    if request.method == "POST":

        address1 = request.POST.get("address1")
        address2 = request.POST.get("address2")

        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")

        payment = request.POST.get("payment")

        for item in cart_items:

            Order.objects.create(

                product=item.product,
                buyer=request.user,
                seller=item.product.seller,

                price=item.final_price(),
                quantity=item.quantity,

                address_line1=address1,
                address_line2=address2,

                city=city,
                state=state,
                pincode=pincode,

                payment_method=payment
            )

        cart_items.delete()

        return redirect("orders")

    return render(request,"checkout.html",{

        "cart_items":cart_items,
        "total":total

    })
    
@login_required
def buy_now(request,product_id):

    product = get_object_or_404(Product,id=product_id)

    Order.objects.create(

        product=product,
        buyer=request.user,
        seller=product.seller,

        price=product.price,
        quantity=1

    )

    return redirect("cart")

@login_required
def order_history(request):

    orders = Order.objects.filter(
        buyer=request.user
    ).select_related("product","seller").order_by("-id")

    return render(request,"order_history.html",{

        "orders":orders

    })
    

@login_required
def seller_orders(request):

    profile = Profile.objects.get(user=request.user)

    if not profile.is_seller:
        return redirect("home")

    orders = Order.objects.filter(
        seller=request.user
    ).select_related("product","buyer").order_by("-id")

    return render(request,"seller_orders.html",{

        "orders":orders

    })
    
@login_required
def order_requests(request):

    requests = OrderRequest.objects.filter(
        buyer=request.user,
        status="pending"
    ).select_related("product","seller")

    return render(request,"order_requests.html",{

        "requests":requests

    })
    
@login_required
def accept_order_request(request,request_id):

    req = get_object_or_404(OrderRequest,id=request_id,buyer=request.user)

    if request.method == "POST":

        cart_item,created = Cart.objects.get_or_create(

            user=request.user,
            product=req.product,

            defaults={
                "negotiated_price":req.agreed_price,
                "quantity":1
            }
        )

        if not created:
            cart_item.quantity += 1
            cart_item.negotiated_price = req.agreed_price
            cart_item.save()

        req.status="approved"
        req.save()

        return redirect("cart")

    return render(request,"confirm_order.html",{

        "req":req

    })
    