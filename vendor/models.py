from django.db import models
from django.conf import settings

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('medicine', 'Medicine'),
        ('seeds', 'Seeds'),
        ('fertilizer', 'Fertilizer'),
        ('tools', 'Tools'),
    ]

    name = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    brand = models.CharField(max_length=100)
    measurement_unit = models.CharField(max_length=50)
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_products',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name