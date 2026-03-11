from django.contrib import admin
from django.urls import path
from marketplace import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('admin/', admin.site.urls),

    # Home
    path('', views.home, name='home'),

    # Authentication
    path("register/", views.register, name="register"),
    path("verify/<uidb64>/<token>/", views.verify_email, name="verify_email"),
    path('login/', views.login_view, name='login'),
    path('login-success/', views.login_success, name='login_success'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('profile/', views.profile_settings, name='profile'),

    # Seller
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
    path("upload/", views.upload_product, name="upload_product"),
    path("edit/<int:product_id>/", views.edit_product, name="edit_product"),
    path("delete/<int:product_id>/", views.delete_product, name="delete_product"),

    # ✅ SAVE / UNSAVE
    path('save/<int:product_id>/', views.toggle_save, name='toggle_save'),
    
    #product details
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove-cart/<int:cart_id>/", views.remove_cart, name="remove_cart"),
    
    # Orders
    path("cart/", views.cart_view, name="cart"),
    path("buy-now/<int:product_id>/",views.buy_now),
    path("negotiation-order/<int:product_id>/",views.negotiation_order),
    
    path("cart-plus/<int:cart_id>/",views.cart_plus),
    path("cart-minus/<int:cart_id>/",views.cart_minus),
    path("place-order/",views.place_order),
    path("invoice/<int:order_id>/",views.generate_invoice),

    # ✅ WISHLIST (NEW SAFE ADDITION)
    path('wishlist/', views.wishlist, name='wishlist'),
    path("wishlist-toggle/<int:product_id>/", views.toggle_wishlist, name="wishlist_toggle"),


    # Seller Public Profile
    path('seller/<str:username>/', views.seller_profile, name='seller_profile'),
    
    # Chat
    path("start-chat/<int:product_id>/", views.start_chat, name="start_chat"),
    path("chat/<int:conversation_id>/", views.chat_room, name="chat_room"),
    path("send-message/", views.send_message, name="send_message"),
    path("seller-chats/", views.seller_chats, name="seller_chats"),
    path("buyer-chats/", views.buyer_chats, name="buyer_chats"),
    path("admin-chats/",views.admin_chats,name="admin_chats"),
    path("fetch-messages/<int:conversation_id>/",views.fetch_messages,name="fetch_messages"),
    path("typing-status/",views.typing_status,name="typing_status"),
    path("user-status/<int:user_id>/",views.user_status,name="user_status"),
    
    #oder management
    path("orders/",views.order_history,name="orders"),
    path("seller-orders/",views.seller_orders,name="seller_orders"),
    path("order-requests/",views.order_requests),
    path("accept-request/<int:request_id>/",views.accept_order_request),
    path("checkout/", views.checkout, name="checkout"),
    path("update-cart/", views.update_cart_quantity, name="update_cart_quantity"),
    
    # ================= PASSWORD RESET =================
        path(
            "password-reset/",
            auth_views.PasswordResetView.as_view(
                template_name="password_reset.html"
            ),
            name="password_reset"
        ),

        path(
            "password-reset-sent/",
            auth_views.PasswordResetDoneView.as_view(
                template_name="password_reset_sent.html"
            ),
            name="password_reset_done"
        ),

        path(
            "password-reset-confirm/<uidb64>/<token>/",
            auth_views.PasswordResetConfirmView.as_view(
                template_name="password_reset_confirm.html"
            ),
            name="password_reset_confirm"
        ),

        path(
            "password-reset-complete/",
            auth_views.PasswordResetCompleteView.as_view(
                template_name="password_reset_complete.html"
            ),
            name="password_reset_complete"
        ),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)