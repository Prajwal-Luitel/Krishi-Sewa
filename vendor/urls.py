from django.urls import path
from vendor import views

urlpatterns = [
    path('product/' , views.product, name='product'),
    path('sales/' , views.sales, name='sales'),
    path('addproduct/' , views.add_product, name='addproduct'),
]