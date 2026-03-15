from django.urls import path
from home import views

urlpatterns = [
    path('home/' , views.home, name='home'),
    path('detect/' , views.detect, name='detect'),
    path('products/' , views.products, name='products'),
    path('cart/' , views.cart, name='cart'),
    path('profile/' , views.profile, name='profile'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
]