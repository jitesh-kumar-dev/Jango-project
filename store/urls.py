from django.urls import path
from . import views


urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'products/',
        views.product_list,
        name='product_list'
    ),

    path(
        'products/<slug:slug>/',
        views.product_detail,
        name='product_detail'
    ),

    path(
        'cart/add/',
        views.add_to_cart,
        name='add_to_cart'
    ),

    path(
        'cart/',
        views.cart_view,
        name='cart'
    ),

    path(
        'cart/update/',
        views.update_cart_item,
        name='update_cart_item'
    ),

    path(
        'checkout/',
        views.checkout,
        name='checkout'
    ),

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'profile/',
        views.profile_view,
        name='profile'
    ),
    path(
    'wishlist/toggle/<int:product_id>/',
    views.toggle_wishlist,
    name='toggle_wishlist'
),
path(
    'order/track/<str:order_number>/',
    views.track_order,
    name='track_order'
),
path(
    'admin-analytics/',
    views.admin_analytics,
    name='admin_analytics'
),

]