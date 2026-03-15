from django.urls import path
from vendor import views

urlpatterns = [
    path("product/", views.product, name="product"),
    path("sales/", views.sales, name="sales"),
    path("addproduct/", views.add_product, name="addproduct"),
    path("editproduct/<int:product_id>/", views.edit_product, name="edit_product"),
    path(
        "deleteproduct/<int:product_id>/", views.delete_product, name="delete_product"
    ),
]
