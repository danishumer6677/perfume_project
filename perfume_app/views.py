# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.utils import timezone
from datetime import timedelta
import json
from django.core.mail import send_mail
from django.conf import settings

from .forms import ContactForm
from .models import Contact

from .models import Category, Product, Cart, CartItem, Wishlist, Order, OrderItem, Review
from .forms import CheckoutForm, ReviewForm, NewsletterForm


from django.contrib.auth import login, authenticate
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import CustomUserCreationForm, UserProfileForm, CustomAuthenticationForm
from .models import User

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse


def home(request):
    """Homepage view with featured and best-selling products"""
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    best_selling_products = Product.objects.filter(is_best_seller=True, is_active=True)[:8]
    categories = Category.objects.filter(is_active=True)[:4]

    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = Product.objects.filter(id__in=recently_viewed_ids, is_active=True)

    context = {
        'featured_products': featured_products,
        'best_selling_products': best_selling_products,
        'categories': categories,
        'recently_viewed': recently_viewed,
    }
    return render(request, 'perfumelux/home.html', context)


def product_list(request):
    """Display all products with filtering and sorting options"""
    products = Product.objects.filter(is_active=True)
    category_id = request.GET.get('category')
    sort = request.GET.get('sort', 'name')
    query = request.GET.get('q')

    # Filter by category
    if category_id:
        products = products.filter(category__id=category_id)

    # Search functionality
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Sorting options
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        products = products.order_by('name')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'sort': sort,
        'query': query,
    }
    return render(request, 'perfumelux/products/list.html', context)


def product_detail(request, slug):
    """Product detail view with reviews and related products"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    # related_products = Product.objects.filter(category=product.category, is_active=True)


# Add to recently viewed
    recently_viewed = request.session.get('recently_viewed', [])
    if product.id in recently_viewed:
        recently_viewed.remove(product.id)
    recently_viewed.insert(0, product.id)
    # Keep only the last 5 viewed products
    request.session['recently_viewed'] = recently_viewed[:5]

    # Get reviews
    reviews = product.reviews.filter(active=True).order_by('-created_at')

    # Get related products
    related_products = Product.objects.filter(
        category=product.category, active=True
    ).exclude(id=product.id)[:4]

    # Review form
    review_form = ReviewForm()

    # Check if user has already reviewed this product
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(user=request.user, product=product)
        except Review.DoesNotExist:
            pass

    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'review_form': review_form,
        'user_review': user_review,
    }
    return render(request, 'perfumelux/products/detail.html', context)


@login_required
@require_POST
def add_review(request, product_id):
    """Add a review to a product"""
    product = get_object_or_404(Product, id=product_id, active=True)
    form = ReviewForm(request.POST)

    if form.is_valid():
        # Check if user already reviewed this product
        existing_review = Review.objects.filter(user=request.user, product=product).first()

        if existing_review:
            # Update existing review
            existing_review.rating = form.cleaned_data['rating']
            existing_review.comment = form.cleaned_data['comment']
            existing_review.save()
            messages.success(request, 'Your review has been updated.')
        else:
            # Create new review
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, 'Thank you for your review!')

    return redirect('product_detail', slug=product.slug)


def category_list(request):
    """Display all categories"""
    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'perfumelux/categories/list.html', context)


def category_detail(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_active=True)


    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'perfumelux/categories/detail.html', context)


@login_required
def cart_view(request):
    """Display user's shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product')  # ✅ use related_name="items"

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'perfumelux/cart.html', context)


@login_required
@require_POST
def add_to_cart(request):
    """Add product to cart or update quantity"""
    data = json.loads(request.body)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return JsonResponse({
        'success': True,
        'message': 'Product added to cart',
        'cart_count': cart.get_items_count(),   # ✅ fixed
    })


@login_required
@require_POST
def update_cart_item(request):
    """Update cart item quantity"""
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if quantity <= 0:
        cart_item.delete()
        message = 'Item removed from cart'
    else:
        cart_item.quantity = quantity
        cart_item.save()
        message = 'Cart updated'

    cart = Cart.objects.get(user=request.user)

    return JsonResponse({
        'success': True,
        'message': message,
        'cart_total': cart.get_total_price(),   # ✅ fixed
        'item_total': cart_item.total_price if quantity > 0 else 0,  # ✅ fixed
        'cart_count': cart.get_items_count(),   # ✅ fixed
    })


@login_required
@require_POST
def remove_from_cart(request):
    """Remove item from cart"""
    data = json.loads(request.body)
    item_id = data.get('item_id')

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    cart = Cart.objects.get(user=request.user)

    return JsonResponse({
        'success': True,
        'message': 'Item removed from cart',
        'cart_total': cart.get_total_price(),   # ✅ fixed
        'cart_count': cart.get_items_count(),   # ✅ fixed
    })


@login_required
def wishlist_view(request):
    """Display user's wishlist"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = wishlist.products.filter(is_active=True)  # corrected field

    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'perfumelux/wishlist.html', context)


@login_required
@require_POST
def toggle_wishlist(request):
    """Add or remove product from wishlist"""
    data = json.loads(request.body)
    product_id = data.get('product_id')

    # corrected field name from active to is_active
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(id=product.id).exists():
        wishlist.products.remove(product)
        is_in_wishlist = False
        message = 'Product removed from wishlist'
    else:
        wishlist.products.add(product)
        is_in_wishlist = True
        message = 'Product added to wishlist'

    return JsonResponse({
        'success': True,
        'message': message,
        'is_in_wishlist': is_in_wishlist
    })


@login_required
def checkout(request):
    """Checkout process"""
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product')  # use related_name

    if cart_items.count() == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Calculate totals
            subtotal = cart.get_total_price()
            tax_amount = 0  # add tax rules if needed
            shipping_cost = 0  # add shipping rules
            discount_amount = 0  # add coupon logic if needed
            total = subtotal + tax_amount + shipping_cost - discount_amount

            # Create order
            order = Order.objects.create(
                user=request.user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                zip_code=form.cleaned_data['zip_code'],
                country=form.cleaned_data['country'],
                payment_method=form.cleaned_data['payment_method'],  # ✅ now required
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                discount_amount=discount_amount,
                total=total,
                notes=form.cleaned_data.get('notes', '')
            )

            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )

            # Clear the cart
            cart.items.all().delete()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_confirmation', order_id=order.id)
        else:
            messages.error(request, "There were errors in your form. Please correct them.")
    else:
        # Pre-fill form with user data if available
        initial_data = {
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or '',
            'email': request.user.email or '',
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'perfumelux/checkout.html', context)


@login_required
def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order
    }
    return render(request, 'perfumelux/order_confirmation.html', context)


@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'perfumelux/orders/history.html', context)


@login_required
def order_detail(request, order_id):
    """Order detail view"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order
    }
    return render(request, 'perfumelux/orders/detail.html', context)


def about(request):
    """About page"""
    return render(request, 'perfumelux/about.html')


def contact(request):
    """
    Contact page with form submission.
    Saves message to database and sends email to owner.
    Shows success or error messages on the page.
    """
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save to DB
            contact_obj = form.save()

            # Prepare email
            subject = f"New Contact Form Submission: {contact_obj.subject}"
            message = f"""
You have received a new message from {contact_obj.name} ({contact_obj.email}).

Subject: {contact_obj.subject}

Message:
{contact_obj.message}
"""

            try:
                # Send email to owner
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],
                    fail_silently=False,   # Show errors instead of hiding
                )
                messages.success(request, "✅ Your message has been sent successfully!")
            except Exception as e:
                # Show the actual Gmail error in browser
                messages.error(request, f"❌ Email sending failed: {e}")

            return redirect("contact")  # Redirect to clear POST data
    else:
        form = ContactForm()

    return render(request, "perfumelux/contact.html", {"form": form})


def newsletter_subscribe(request):
    """Newsletter subscription"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            # Here you would typically save to database and send to email service
            # For now, we'll just return a success message
            email = form.cleaned_data['email']
            messages.success(request, f'Thank you for subscribing with {email}!')
            return redirect('home')

    return redirect('home')


def search(request):
    """Search products"""
    query = request.GET.get('q', '')

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True  # <-- corrected field name
        ).order_by('name')
    else:
        products = Product.objects.none()

    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'perfumelux/search.html', context)


# API views for AJAX functionality
@login_required
def get_cart_count(request):
    """Get cart item count for navbar icon"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    return JsonResponse({'count': cart.get_items_count()})


@login_required
def check_wishlist_status(request, product_id):
    """Check if product is in user's wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    is_in_wishlist = wishlist.products.filter(id=product.id).exists()

    return JsonResponse({'is_in_wishlist': is_in_wishlist})


def product_quick_view(request, product_id):
    """Quick view modal content"""
    product = get_object_or_404(Product, id=product_id, active=True)
    return render(request, 'perfumelux/products/quick_view.html', {'product': product})



def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Authenticate using email
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, email=email, password=password)  # ✅ use email here

            if user is not None:
                login(request, user)
                messages.success(request, '🎉 Account created successfully! Welcome to PerfumeLux.')

                from .models import Cart, Wishlist
                Cart.objects.get_or_create(user=user)
                Wishlist.objects.get_or_create(user=user)

                return redirect('home')
            else:
                messages.error(request, 'Authentication failed after registration.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'perfumelux/auth/register.html', {'form': form})



@login_required
def profile(request):
    """User profile view"""
    user = request.user
    orders = user.order_set.all().order_by('-created_at')[:5]
    wishlist_count = user.wishlist_set.first().products.count() if hasattr(user, 'wishlist_set') and user.wishlist_set.exists() else 0
    review_count = user.review_set.count()

    context = {
        'user': user,
        'recent_orders': orders,
        'wishlist_count': wishlist_count,
        'review_count': review_count,
    }
    return render(request, 'perfumelux/auth/profile.html', context)


@login_required
def profile_update(request):
    """Update user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'perfumelux/auth/profile_update.html', {'form': form})


@login_required
def order_history(request):
    """Display user's order history"""
    orders = request.user.order_set.all().order_by('-created_at')

    # Add status to orders for display purposes
    for order in orders:
        if not hasattr(order, 'status'):
            # Set a default status based on order age for demonstration
            from django.utils import timezone
            from datetime import timedelta
            if timezone.now() - order.created_at > timedelta(days=7):
                order.status = 'delivered'
            elif timezone.now() - order.created_at > timedelta(days=2):
                order.status = 'shipped'
            else:
                order.status = 'processing'

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'perfumelux/orders/history.html', context)


@login_required
def reorder(request, order_id):
    """Reorder items from a previous order"""
    from django.http import JsonResponse
    from .models import Cart, CartItem, Order

    try:
        order = Order.objects.get(id=order_id, user=request.user)
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Add all items from the order to the cart
        for order_item in order.orderitem_set.all():
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=order_item.product,
                defaults={'quantity': order_item.quantity}
            )
            if not created:
                cart_item.quantity += order_item.quantity
                cart_item.save()

        cart_count = cart.get_items_count()

        return JsonResponse({
            'success': True,
            'message': 'Items added to cart successfully',
            'cart_count': cart_count
        })

    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        }, status=404)


# Custom Password Reset Views with neumorphic styling context
class CustomPasswordResetView(PasswordResetView):
    template_name = 'perfumelux/auth/password_reset.html'
    email_template_name = 'perfumelux/auth/password_reset_email.html'
    subject_template_name = 'perfumelux/auth/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        messages.info(self.request, 'Password reset instructions have been sent to your email.')
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'perfumelux/auth/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'perfumelux/auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been reset successfully. You can now login with your new password.')
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'perfumelux/auth/password_reset_complete.html'


# Additional authentication-related views
def auth_login(request):
    """Custom login view with messages"""
    if request.user.is_authenticated:
        return redirect('home')

    form = CustomAuthenticationForm()

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')

                # Redirect to next page if specified, otherwise home
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'perfumelux/auth/login.html', {'form': form})


def auth_logout(request):
    """Custom logout view"""
    from django.contrib.auth import logout
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'You have been successfully logged out.')
    return render(request, 'perfumelux/auth/logout.html')


@login_required
def account_settings(request):
    """Account settings page"""
    return render(request, 'perfumelux/auth/account_settings.html', {
        'user': request.user
    })


@login_required
def delete_account(request):
    """Delete account view"""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')

    return render(request, 'perfumelux/auth/delete_account_confirm.html')


@login_required
@require_POST
def toggle_newsletter(request):
    """Toggle newsletter subscription"""
    from django.http import JsonResponse
    import json

    data = json.loads(request.body)
    subscribed = data.get('subscribed', False)

    request.user.newsletter_subscribed = subscribed
    request.user.save()

    return JsonResponse({
        'success': True,
        'message': 'Newsletter preference updated',
        'subscribed': subscribed
    })


def shipping_policy(request):
    """Shipping policy page"""
    return render(request, 'perfumelux/policies/shipping.html')


def returns_exchanges(request):
    """Returns and exchanges policy page"""
    return render(request, 'perfumelux/policies/returns.html')


def faq(request):
    """Frequently Asked Questions page"""
    return render(request, 'perfumelux/policies/faq.html')


def privacy_policy(request):
    """Privacy policy page"""
    return render(request, 'perfumelux/policies/privacy.html')
