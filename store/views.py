from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login
import uuid
import json
from decouple import config
import google.generativeai as genai

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem,
    Wishlist, WishlistItem
)

from .forms import (
    ProductReviewForm, CheckoutForm, RegisterForm, ProfileForm
)


def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:12]
    categories = Category.objects.filter(is_active=True)[:6]

    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    })


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.filter(is_active=True)

    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    sort = request.GET.get('sort')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)

    if sort == 'low':
        products = products.order_by('price')
    elif sort == 'high':
        products = products.order_by('-price')
    elif sort == 'latest':
        products = products.order_by('-created_at')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'products/list.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'category_slug': category_slug,
        'sort': sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.all()[:10]

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]

    in_wishlist = False
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            in_wishlist = WishlistItem.objects.filter(
                wishlist=wishlist,
                product=product
            ).exists()

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
        'in_wishlist': in_wishlist,
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
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    item = WishlistItem.objects.filter(
        wishlist=wishlist,
        product=product
    ).first()

    if item:
        item.delete()
        messages.success(request, f'{product.name} removed from wishlist.')
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        messages.success(request, f'{product.name} added to wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    wishlist = Wishlist.objects.filter(user=request.user).first()
    wishlist_items = wishlist.items.select_related('product') if wishlist else []

    total_orders = orders.count()
    total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0

    latest_order = orders.first()

    return render(request, 'store/dashboard.html', {
        'orders': orders,
        'wishlist_items': wishlist_items,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'latest_order': latest_order,
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

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


def cart_total(cart):
    if not cart:
        return 0

    return sum(item.total_price for item in cart.items.all())


def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        count = cart.items.count() if cart else 0
    else:
        count = request.session.get('cart_count', 0)

    return {'cart_count': count}
@login_required
def track_order(request, order_number):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )

    return render(request, 'store/track_order.html', {
        'order': order
    })
@staff_member_required
def admin_analytics(request):
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(
        revenue=Sum('total_amount')
    )['revenue'] or 0

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    top_products = OrderItem.objects.values(
        'product__name'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]

    status_data = Order.objects.values(
        'status'
    ).annotate(
        count=Count('id')
    )

    product_names = [item['product__name'] for item in top_products]
    product_sales = [item['total_sold'] for item in top_products]

    status_labels = [item['status'] for item in status_data]
    status_counts = [item['count'] for item in status_data]

    return render(request, 'store/admin_analytics.html', {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'product_names': product_names,
        'product_sales': product_sales,
        'status_labels': status_labels,
        'status_counts': status_counts,
    })
@require_http_methods(["POST"])
def ai_chatbot(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
    except Exception:
        return JsonResponse({
            "reply": "Please send a valid message."
        })

    if not user_message:
        return JsonResponse({
            "reply": "Please type or speak what you want to buy."
        })

    products = Product.objects.filter(
        is_active=True
    ).select_related("category")[:30]

    product_list = []

    for product in products:
        product_list.append(
            f"Name: {product.name}, "
            f"Category: {product.category.name}, "
            f"Price: ₹{product.get_price}, "
            f"Stock: {product.stock}"
        )

    products_text = "\n".join(product_list)

    api_key = config("GEMINI_API_KEY", default="")

    if not api_key:
        return JsonResponse({
            "reply": "AI key is not configured. Please add GEMINI_API_KEY in .env file."
        })

    prompt = f"""
You are an AI shopping assistant for an ecommerce website named Jitesh Store.

Your job:
- Help users find products.
- Recommend products only from the available product list.
- Reply in simple English.
- Keep answer short and useful.
- If user asks in Hindi, reply in simple Hindi.
- If matching products are found, suggest product names and price.
- If no product matches, suggest searching another keyword.

Available products:
{products_text}

User message:
{user_message}
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return JsonResponse({
            "reply": response.text
        })

    except Exception as e:
        return JsonResponse({
            "reply": f"AI error: {str(e)}"
        })
