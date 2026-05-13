from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
import uuid

from .models import (
    Product,
    Category,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Wishlist
)

from .forms import (
    ProductReviewForm,
    CheckoutForm,
    RegisterForm,
    ProfileForm
)


def home(request):
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    )[:8]

    latest_products = Product.objects.filter(
        is_active=True
    ).order_by('-created_at')[:12]

    categories = Category.objects.filter(
        is_active=True
    )[:6]

    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    })


def product_list(request):
    products = Product.objects.filter(
        is_active=True
    ).select_related('category')

    query = request.GET.get('q')
    category_slug = request.GET.get('category')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_active=True
        )
        products = products.filter(category=category)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    categories = Category.objects.filter(is_active=True)

    return render(request, 'products/list.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'category_slug': category_slug,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
        is_active=True
    )

    reviews = product.reviews.all()[:10]

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]

    if request.method == 'POST':
        form = ProductReviewForm(request.POST)

        if form.is_valid() and request.user.is_authenticated:
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

            messages.success(request, 'Review submitted successfully!')
            return redirect('product_detail', slug=slug)
    else:
        form = ProductReviewForm()

    return render(request, 'products/detail.html', {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'form': form,
    })


@login_required
def add_to_cart(request):
    product_id = request.GET.get('product_id')
    quantity = int(request.GET.get('quantity', 1))

    product = get_object_or_404(Product, id=product_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart')


@login_required
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    total = cart_total(cart) if cart else 0

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'total': total,
    })


@require_http_methods(["POST"])
@login_required
def update_cart_item(request):
    cart_item_id = request.POST.get('cart_item_id')
    quantity = int(request.POST.get('quantity'))

    cart_item = get_object_or_404(
        CartItem,
        id=cart_item_id,
        cart__user=request.user
    )

    if quantity == 0:
        cart_item.delete()
        return JsonResponse({'status': 'removed'})

    cart_item.quantity = quantity
    cart_item.save()

    return JsonResponse({
        'status': 'success',
        'total': str(cart_item.total_price)
    })


@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                order_number=f'ORDER_{uuid.uuid4().hex[:8].upper()}',
                total_amount=cart_total(cart),
                shipping_address=(
                    f"{form.cleaned_data['address']}, "
                    f"{form.cleaned_data['city']}, "
                    f"{form.cleaned_data['postal_code']}, "
                    f"{form.cleaned_data['country']}"
                )
            )

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.get_price
                )

            cart.items.all().delete()

            messages.success(request, 'Order placed successfully!')
            return redirect('dashboard')
    else:
        form = CheckoutForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })

    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'form': form,
        'total': cart_total(cart),
    })


@login_required
def dashboard(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    wishlist = Wishlist.objects.filter(user=request.user).first()
    wishlist_items = wishlist.items.all() if wishlist else []

    return render(request, 'store/dashboard.html', {
        'orders': orders,
        'wishlist_items': wishlist_items,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form
    })


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form
    })


def cart_total(cart):
    if not cart:
        return 0

    return sum(
        item.total_price
        for item in cart.items.all()
    )


def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        count = cart.items.count() if cart else 0
    else:
        count = request.session.get('cart_count', 0)

    return {
        'cart_count': count
    }
