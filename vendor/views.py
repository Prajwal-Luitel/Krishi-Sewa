# Create your views here.
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from .models import Product

def product(request):
    products = Product.objects.all()
    context = {"products": products}
    return render(request, "product.html", context=context)

def sales(request):
    return render(request, "sales.html")

def add_product(request):
    if request.method == 'POST':
        try:
            # Extract all form data
            name = request.POST.get('name')
            description = request.POST.get('description')
            category = request.POST.get('category')
            selling_price = request.POST.get('selling_price')  
            cost_price = request.POST.get('cost_price') or 0  
            stock = request.POST.get('stock')
            brand = request.POST.get('brand')
            measurement_unit = request.POST.get('unit')
            
            # Get the uploaded image
            image = request.FILES.get('product_image')
            
            # Validate required fields
            if not all([name, description, category, selling_price, stock]):
                messages.error(request, 'Please fill in all required fields.')
                context = { 'old': request.POST }
                return render(request, 'addproduct.html',  context=context)
            
            # Create and save the product
            product = Product(
                name=name,
                description=description,
                category=category,
                selling_price=selling_price,
                cost_price=cost_price,  
                stock=stock,
                brand=brand if brand else '',
                measurement_unit=measurement_unit if measurement_unit else 'kg',
                image=image if image else None
            )
            product.save()
            
            messages.success(request, f'Product "{name}" added successfully!')
            return redirect('product')  
            
        except Exception as e:
            messages.error(request, f'Error saving product: {str(e)}')
    
    # If GET request, just render the form
    return render(request, 'addproduct.html')