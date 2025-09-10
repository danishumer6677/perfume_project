# urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm
from .views import (
    CustomPasswordResetView, CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView, CustomPasswordResetCompleteView
)


urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/quick-view/', views.product_quick_view, name='product_quick_view'),
    path('products/<int:product_id>/review/', views.add_review, name='add_review'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),

    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/check/<int:product_id>/', views.check_wishlist_status, name='check_wishlist_status'),

    path('checkout/', views.checkout, name='checkout'),
    path('checkout/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),

    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    path('search/', views.search, name='search'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

    # API endpoints
    path('api/cart/count/', views.get_cart_count, name='get_cart_count'),


    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.auth_login, name='login'),
    path('logout/', views.auth_logout, name='logout'),

    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/settings/', views.account_settings, name='account_settings'),
    path('profile/delete/', views.delete_account, name='delete_account'),

    # Password reset URLs
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Order reorder functionality
    path('orders/<int:order_id>/reorder/', views.reorder, name='reorder'),

    path('api/toggle-newsletter/', views.toggle_newsletter, name='toggle_newsletter'),

    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('returns-exchanges/', views.returns_exchanges, name='returns_exchanges'),
    path('faq/', views.faq, name='faq'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
