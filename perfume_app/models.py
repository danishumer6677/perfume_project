from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
import uuid
from django.contrib.auth.models import AbstractUser

class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Category(TimeStampedModel):
    """Product category model"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

class Product(TimeStampedModel):
    """Product model for perfumes"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Original price for display when product is on sale"
    )
    cost_per_ml = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Automatically calculated cost per milliliter"
    )

    # Inventory
    sku = models.CharField(max_length=100, unique=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5, help_text="Alert when stock falls below this number")

    # Flags (views.py expects these names!)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)

    # Fragrance details
    fragrance_notes = models.TextField(help_text="Top, middle, and base notes separated by commas")
    intensity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Fragrance intensity from 1 (light) to 5 (strong)"
    )
    longevity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Longevity from 1 (short) to 5 (long-lasting)"
    )

    # Sizes available
    SIZE_CHOICES = [
        (30, '30ml'),
        (50, '50ml'),
        (75, '75ml'),
        (100, '100ml'),
        (125, '125ml'),
        (150, '150ml'),
    ]
    size = models.PositiveIntegerField(choices=SIZE_CHOICES, default=100)

    # Gender targeting
    GENDER_CHOICES = [
        ('M', 'Men'),
        ('W', 'Women'),
        ('U', 'Unisex'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_size_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        # Generate SKU if not provided
        if not self.sku:
            base_sku = f"{self.category.name[:3].upper()}-{self.name[:3].upper()}-{self.size}"
            self.sku = slugify(base_sku).upper()

        # Calculate cost per ml if price and size are available
        if self.price and self.size:
            self.cost_per_ml = self.price / self.size

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return round(discount)
        return 0

    def average_rating(self):
        reviews = self.reviews.filter(is_active=True)
        if reviews.exists():
            return round(reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'], 1)
        return 0

    def review_count(self):
        return self.reviews.filter(is_active=True).count()

class ProductImage(TimeStampedModel):
    """Product images model"""
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'is_primary', '-created_at']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # If this is set as primary, ensure no other images are primary
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)

class Review(TimeStampedModel):
    """Product reviews model"""
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_active = models.BooleanField(default=True)
    verified_purchase = models.BooleanField(default=False)

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

class Cart(TimeStampedModel):
    """Shopping cart model"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_items_count(self):
        """Total quantity of all items"""
        return sum(item.quantity for item in self.items.all())

    def get_total(self):
        """Total price of all items in cart"""
        return sum(item.total_price for item in self.items.all())

    # ✅ For Django Admin readability
    @property
    def total_items(self):
        return self.get_items_count()

    @property
    def subtotal(self):
        return self.get_total()

    @property
    def total(self):
        """Modify here if you want to add tax/shipping later"""
        return self.get_total()

    def get_total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(TimeStampedModel):
    """Shopping cart item model"""
    cart = models.ForeignKey(
        Cart, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "Product", related_name="cart_items", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def total_price(self):
        """Total price for this item"""
        return self.product.price * self.quantity

class Wishlist(TimeStampedModel):
    """User wishlist model"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='wishlists')

    def __str__(self):
        return f"Wishlist for {self.user.username}"

    @property
    def product_count(self):
        return self.products.count()

class Order(TimeStampedModel):
    """Order model"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cod', 'Cash on Delivery'),
    ]

    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Customer information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Shipping address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    # Order details
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)

    # Financial details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)


    # Additional information
    notes = models.TextField(blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_date = models.DateTimeField(blank=True, null=True)
    delivered_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} by {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_str = timezone.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4().int)[:8]
            self.order_number = f"ORD-{date_str}-{unique_id}"

        if not self.total:
            self.total = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount

        super().save(*args, **kwargs)

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']

    @property
    def item_count(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

class OrderItem(TimeStampedModel):
    """Order item model"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in order #{self.order.order_number}"

    @property
    def total_price(self):
        return self.price * self.quantity

class NewsletterSubscriber(TimeStampedModel):
    """Newsletter subscription model"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    token = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid4())
        super().save(*args, **kwargs)

class SiteSettings(TimeStampedModel):
    """Site settings model"""
    site_name = models.CharField(max_length=100, default="PerfumeLux")
    site_description = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(default="info@perfumelux.com")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Social media links
    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    tiktok_url = models.URLField(blank=True, null=True)

    # Store settings
    currency = models.CharField(max_length=10, default="USD")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    standard_shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=5.99)

    # SEO settings
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            return SiteSettings.objects.first()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Site Settings"


class User(AbstractUser):
    # Remove username
    username = None

    # Use email as unique identifier
    email = models.EmailField(unique=True)

    # Extra fields
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    newsletter_subscribed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []   # removes username requirement

    def __str__(self):
        return self.email


class Contact(models.Model):
    SUBJECT_CHOICES = [
        ('product', 'Product Inquiry'),
        ('order', 'Order Support'),
        ('shipping', 'Shipping Question'),
        ('return', 'Returns & Exchanges'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.subject}"
