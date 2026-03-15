# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product

def product(request):
    products = Product.objects.all()
    total_products = products.count()
    in_stock_count = products.filter(stock__gt=0).count()
    out_of_stock_count = products.filter(stock=0).count()
    context = {
        "products": products,
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
    }
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


def edit_product(request, product_id):
    prod = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        try:
            prod.name = request.POST.get('name')
            prod.description = request.POST.get('description')
            prod.category = request.POST.get('category')
            prod.selling_price = request.POST.get('selling_price')
            prod.stock = request.POST.get('stock')
            prod.brand = request.POST.get('brand', '')
            prod.measurement_unit = request.POST.get('unit', 'kg')
            image = request.FILES.get('product_image')
            if image:
                prod.image = image
            prod.save()
            messages.success(request, f'Product "{prod.name}" updated successfully!')
            return redirect('product')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
            context = {'product': prod, 'old': request.POST}
            return render(request, 'addproduct.html', context=context)
    context = {'product': prod}
    return render(request, 'addproduct.html', context=context)


def delete_product(request, product_id):
    if request.method == 'POST':
        prod = get_object_or_404(Product, id=product_id)
        name = prod.name
        prod.delete()
        messages.success(request, f'Product "{name}" deleted successfully!')
    return redirect('product')