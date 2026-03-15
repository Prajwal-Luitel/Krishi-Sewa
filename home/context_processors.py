from home.models import Cart


def cart_count(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return {'cart_count': cart.total_items}
    return {'cart_count': 0}
