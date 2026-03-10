from django.contrib import admin
from django.urls import path
from marketplace import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

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

    # Seller
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
    path("upload/", views.upload_product, name="upload_product"),
    path("edit/<int:product_id>/", views.edit_product, name="edit_product"),
    path("delete/<int:product_id>/", views.delete_product, name="delete_product"),

    # ✅ SAVE / UNSAVE
    path('save/<int:product_id>/', views.toggle_save, name='toggle_save'),

    # ✅ WISHLIST (NEW SAFE ADDITION)
    path('wishlist/', views.wishlist, name='wishlist'),
    path("wishlist-toggle/<int:product_id>/", views.toggle_wishlist, name="wishlist_toggle"),

    path("seller/settings/", views.seller_settings, name="seller_settings"),
    path("profile/settings/", views.profile_settings, name="profile_settings"),


    # Seller Public Profile
    path('seller/<str:username>/', views.seller_profile, name='seller_profile'),

    # Chat
    path('chat/<int:product_id>/', views.chat_view, name='chat'),
    path('send-message/', views.send_message, name='send_message'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)