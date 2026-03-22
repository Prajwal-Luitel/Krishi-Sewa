import os
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from vendor.models import Product
from home.models import Cart, CartItem
from home.services.rag import build_disease_rag_output
from ultralytics import YOLO
from django.contrib.auth.decorators import login_required
from PIL import Image
import io
import base64

DETECT_SESSION_KEY = 'detect_last_result'

# Load YOLO model - path relative to this file's location
model_path = os.path.join(os.path.dirname(__file__), 'model', 'best.pt')
model = YOLO(model_path)

# Use GPU if available 
try:
    model.to('cuda')
except Exception:
    pass  # Continue with CPU if CUDA is not available   


def _guide_summary():
    return {
        'overview': 'Upload a clear leaf image and click Detect. The system identifies likely disease class and then generates a structured summary.',
        'symptoms': [
            'Capture one leaf per image for better detection quality',
            'Use good lighting and avoid blurry photos',
            'Keep the diseased area visible in the frame',
            'After detection, review confidence before taking action',
        ],
        'prevention': [
            'Use the recommendations as guidance, not final diagnosis',
            'Compare symptoms in-field before treatment',
            'Start with safe and crop-appropriate products',
            'Consult local experts for severe spread conditions',
        ],
        'recommendation_reason': 'Recommendations appear only after you run detection.',
    }


def _no_detection_summary():
    return {
        'overview': 'No clear disease was detected in this image. Please upload a clearer close-up leaf image and try again.',
        'symptoms': [
            'Focus on one affected leaf in the frame',
            'Use bright natural light and avoid shadows',
            'Keep the camera steady to avoid blur',
            'Capture visible spots, lesions, or discoloration',
        ],
        'prevention': [
            'Continue regular field monitoring',
            'Isolate suspicious plants early if symptoms appear',
            'Maintain balanced irrigation and crop hygiene',
            'Consult an agronomist if symptoms persist',
        ],
        'recommendation_reason': 'No recommendations shown because no disease could be confidently detected.',
    }


def _get_products_from_ids(product_ids):
    if not product_ids:
        return []
    products = Product.objects.filter(id__in=product_ids)
    product_map = {p.id: p for p in products}
    return [product_map[pid] for pid in product_ids if pid in product_map][:3]


@login_required(login_url='login')
def detect(request):
    context = {
        'summary': _guide_summary(),
        'recommended_products': [],
        'has_detected': False,
    }

    if request.method == 'GET':
        saved_result = request.session.get(DETECT_SESSION_KEY)
        if saved_result:
            context['summary'] = saved_result.get('summary', _guide_summary())
            context['detections'] = saved_result.get('detections', [])
            context['primary_disease'] = saved_result.get('primary_disease')
            context['primary_confidence'] = saved_result.get('primary_confidence')
            context['original_image'] = saved_result.get('original_image')
            context['recommended_products'] = _get_products_from_ids(
                saved_result.get('recommended_product_ids', [])
            )
            context['has_detected'] = True
        return render(request, 'detect.html', context)
    
    if request.method == "POST":
        # Get the uploaded image
        if 'imageInput' not in request.FILES:
            context['error'] = 'No image provided'
            return render(request, "detect.html", context)
        
        image_file = request.FILES['imageInput']
        
        # Open the image
        img = Image.open(image_file)
        img_array = img.convert('RGB')  # Ensure RGB format
        
        # Convert original image to base64
        buffer_orig = io.BytesIO()
        img.save(buffer_orig, format='PNG')
        orig_img_str = base64.b64encode(buffer_orig.getvalue()).decode()
        context['original_image'] = f'data:image/png;base64,{orig_img_str}'
        
        # Run YOLO inference
        results = model.predict(img_array, conf=0.25)
        
        # Extract detection info
        detections = []
        if results[0].boxes is not None:
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = results[0].names[cls_id]
                detections.append({
                    'class': class_name,
                    'confidence': f"{confidence*100:.2f}%"
                })

        detections = sorted(
            detections,
            key=lambda d: float(d['confidence'].replace('%', '')),
            reverse=True,
        )
        top_detection = detections[0] if detections else None
        if top_detection:
            disease_name = top_detection['class']
            summary, recommended_products = build_disease_rag_output(disease_name)
            primary_confidence = top_detection['confidence']
        else:
            disease_name = None
            summary = _no_detection_summary()
            recommended_products = []
            primary_confidence = None
        
        # Pass result to template
        context['detections'] = detections
        context['summary'] = summary
        context['recommended_products'] = recommended_products
        context['primary_disease'] = disease_name
        context['primary_confidence'] = primary_confidence
        context['has_detected'] = True

        request.session[DETECT_SESSION_KEY] = {
            'summary': summary,
            'detections': detections,
            'primary_disease': disease_name,
            'primary_confidence': primary_confidence,
            'recommended_product_ids': [p.id for p in recommended_products],
            'original_image': context.get('original_image'),
        }
        request.session.modified = True
    
    return render(request, "detect.html", context)

@login_required(login_url='login')
def products(request):
    products = Product.objects.all()

    # Search filter
    search_query = request.GET.get('q', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    # Category filter
    selected_categories = request.GET.getlist('category')
    if selected_categories:
        products = products.filter(category__in=selected_categories)

    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(selling_price__gte=min_price)
    if max_price:
        products = products.filter(selling_price__lte=max_price)

    # Sort
    sort_by = request.GET.get('sort_by', 'price_asc')
    if sort_by == 'price_desc':
        products = products.order_by('-selling_price')
    else:
        products = products.order_by('selling_price')

    context = {
        "products": products,
        "selected_categories": selected_categories,
        "sort_by": sort_by,
        "min_price": min_price or '',
        "max_price": max_price or '',
        "search_query": search_query,
    }
    return render(request, "products.html", context=context)

@login_required(login_url='login')
def home(request):
    products = Product.objects.all()[:4]
    context = {'products': products}
    return render(request, "home.html", context)

@login_required(login_url='login')
def cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, "cart.html", context)


@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


@login_required(login_url='login')
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
    return redirect('cart')


@login_required(login_url='login')
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    return redirect('cart')

@login_required(login_url='login')
def profile(request):
    from django.contrib.auth import get_user_model
    from django.contrib import messages
    
    User = get_user_model()
    user = request.user
    context = {}
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        profile_pic = request.FILES.get('profile_pic')
        
        errors = {}
        
        # Validate required fields
        if not name:
            errors['name'] = 'Name is required'
        if not username:
            errors['username'] = 'Username is required'
        if not email:
            errors['email'] = 'Email is required'
        
        # Check if username is unique (excluding current user)
        if username and User.objects.filter(username=username).exclude(pk=user.pk).exists():
            errors['username'] = 'Username already exists'
        
        # Check if email is unique (excluding current user)
        if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
            errors['email'] = 'Email already exists'
        
        if errors:
            context['errors'] = errors
            context['form_data'] = {
                'name': name,
                'username': username,
                'email': email,
            }
        else:
            # Split name into first_name and last_name
            name_parts = name.split(maxsplit=1)
            user.first_name = name_parts[0] if len(name_parts) > 0 else ''
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.username = username
            user.email = email
            
            # Handle profile picture upload
            if profile_pic:
                user.profile_pic = profile_pic
            
            user.save()
            
            context['success'] = True
            context['success_message'] = 'Profile updated successfully!'
    
    return render(request, "profile.html", context)