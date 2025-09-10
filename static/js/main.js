// main.js
document.addEventListener('DOMContentLoaded', function() {
    // Sticky header on scroll
    window.addEventListener('scroll', function() {
        const header = document.querySelector('header');
        header.classList.toggle('scrolled', window.scrollY > 100);
    });

    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            hamburger.classList.toggle('active');
        });
    }

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (navLinks && navLinks.classList.contains('active') &&
            !event.target.closest('.nav-links') &&
            !event.target.closest('.hamburger')) {
            navLinks.classList.remove('active');
            hamburger.classList.remove('active');
        }
    });

    // Cart functionality
    const updateCartCount = function(count) {
        const cartCount = document.getElementById('cart-count');
        if (cartCount) {
            cartCount.textContent = count;
        }
    };

    // Add to cart functionality
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const quantity = this.dataset.quantity || 1;
            addToCart(productId, quantity);
        });
    });

    // Wishlist functionality
    document.querySelectorAll('.wishlist').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            toggleWishlist(productId);
        });
    });

    // Quantity selectors
    document.querySelectorAll('.qty-btn').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input[type="number"]');
            if (input) {
                let value = parseInt(input.value);
                if (this.classList.contains('increase')) {
                    input.value = value + 1;
                } else if (this.classList.contains('decrease') && value > 1) {
                    input.value = value - 1;
                }

                // Trigger change event
                const event = new Event('change', { bubbles: true });
                input.dispatchEvent(event);
            }
        });
    });

    // Image gallery functionality
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.addEventListener('click', function() {
            const mainImage = document.getElementById('main-product-image');
            if (mainImage) {
                mainImage.src = this.dataset.image;
            }

            // Update active thumbnail
            document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!valid) {
                e.preventDefault();
                this.querySelector('.is-invalid').focus();
            }
        });
    });

    // Search functionality
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');

    if (searchInput && searchBtn) {
        const performSearch = function() {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/search/?q=${encodeURIComponent(query)}`;
            }
        };

        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }

    // Filter and sort functionality
    const categoryFilter = document.getElementById('category-filter');
    const sortFilter = document.getElementById('sort-filter');

    if (categoryFilter) {
        categoryFilter.addEventListener('change', updateFilters);
    }

    if (sortFilter) {
        sortFilter.addEventListener('change', updateFilters);
    }

    function updateFilters() {
        const category = categoryFilter ? categoryFilter.value : '';
        const sort = sortFilter ? sortFilter.value : '';
        const query = searchInput ? searchInput.value : '';

        let url = window.location.pathname + '?';
        if (category) url += `category=${category}&`;
        if (sort) url += `sort=${sort}&`;
        if (query) url += `q=${encodeURIComponent(query)}&`;

        window.location.href = url.slice(0, -1); // Remove trailing & or ?
    }

    // Initialize animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, observerOptions);

    // Observe elements for animation
    document.querySelectorAll('.category-card, .product-card, .section-title').forEach(element => {
        observer.observe(element);
    });

    // Newsletter subscription
    const newsletterForm = document.querySelector('.newsletter form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;

            // Simple email validation
            if (!validateEmail(email)) {
                showMessage('Please enter a valid email address', 'error');
                return;
            }

            // Simulate subscription
            this.querySelector('button').disabled = true;
            this.querySelector('button').textContent = 'Subscribing...';

            setTimeout(() => {
                showMessage('Thank you for subscribing to our newsletter!', 'success');
                this.reset();
                this.querySelector('button').disabled = false;
                this.querySelector('button').textContent = 'Subscribe';
            }, 1000);
        });
    }

    // Utility functions
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function showMessage(message, type = 'info') {
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `alert alert-${type}`;
        messageEl.textContent = message;

        // Add to messages container
        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            messagesContainer.appendChild(messageEl);

            // Remove after 5 seconds
            setTimeout(() => {
                messageEl.remove();
            }, 5000);
        }
    }

    // CSRF token for AJAX requests
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];

        return cookieValue || '';
    }

    // AJAX functions
    window.addToCart = function(productId, quantity = 1) {
        fetch('/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartCount(data.cart_count);
                showMessage(data.message, 'success');
            } else {
                showMessage('Failed to add item to cart', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred', 'error');
        });
    };

    window.toggleWishlist = function(productId) {
        fetch('/wishlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                product_id: productId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');

                // Update heart icon if needed
                const heartIcon = document.querySelector(`.wishlist[data-product-id="${productId}"] i`);
                if (heartIcon) {
                    if (data.is_in_wishlist) {
                        heartIcon.className = 'fas fa-heart';
                    } else {
                        heartIcon.className = 'far fa-heart';
                    }
                }
            } else {
                showMessage('Failed to update wishlist', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred', 'error');
        });
    };
});
