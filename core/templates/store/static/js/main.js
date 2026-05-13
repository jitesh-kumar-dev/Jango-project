// MAIN JAVASCRIPT FOR JITESH STORE

document.addEventListener('DOMContentLoaded', function () {

    // CART AJAX SUPPORT

    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function (e) {

            const productId = this.dataset.productId;

            if (!productId) {
                return;
            }

            e.preventDefault();

            fetch(`/cart/add/?product_id=${productId}&quantity=1`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;

                if (data.status === 'success') {
                    showToast(data.message, 'success');
                    updateCartCount(data.cart_count);
                }
            })
            .catch(() => {
                window.location.href = `/cart/add/?product_id=${productId}&quantity=1`;
            });
        });
    });


    // QUANTITY UPDATE

    document.querySelectorAll('.quantity-update').forEach(button => {
        button.addEventListener('click', function () {

            const input = this.parentNode.querySelector('input[type="number"]');

            if (!input) return;

            const cartItemId = input.dataset.cartItemId;

            let quantity = parseInt(input.value);

            if (this.classList.contains('increment')) {
                quantity++;
            } else {
                quantity--;
                if (quantity < 1) {
                    quantity = 1;
                }
            }

            input.value = quantity;

            updateCartItem(cartItemId, quantity);
        });
    });


    // REMOVE CART ITEM

    document.querySelectorAll('.remove-cart-item').forEach(button => {
        button.addEventListener('click', function () {

            if (confirm('Remove this item from cart?')) {
                const cartItemId = this.dataset.cartItemId;
                updateCartItem(cartItemId, 0);
            }

        });
    });


    // PAYMENT METHOD SELECTION

    document.querySelectorAll('.payment-card').forEach(card => {
        card.addEventListener('click', function () {

            document.querySelectorAll('.payment-card').forEach(c => {
                c.classList.remove('active');
            });

            this.classList.add('active');

            const paymentInput = document.querySelector('input[name="payment_method"]');

            if (paymentInput) {
                paymentInput.value = this.dataset.method;
            }

        });
    });


    // DARK MODE

    const themeToggle = document.getElementById('themeToggle');

    if (themeToggle) {

        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-mode');
            themeToggle.textContent = '☀️ Light';
        }

        themeToggle.addEventListener('click', function () {
            document.body.classList.toggle('dark-mode');

            if (document.body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
                themeToggle.textContent = '☀️ Light';
            } else {
                localStorage.setItem('theme', 'light');
                themeToggle.textContent = '🌙 Dark';
            }
        });
    }


    // AI SHOPPING ASSISTANT

    const aiToggle = document.getElementById('aiAssistantToggle');
    const aiPanel = document.getElementById('aiAssistantPanel');
    const aiSearch = document.getElementById('aiAssistantSearch');
    const aiInput = document.getElementById('aiAssistantInput');
    const aiReply = document.getElementById('aiAssistantReply');
    const aiVoiceBtn = document.getElementById('aiVoiceBtn');

    if (aiToggle && aiPanel) {
        aiToggle.addEventListener('click', function () {
            aiPanel.classList.toggle('active');
        });
    }

    function runAISearch() {
        if (!aiInput || !aiReply) return;

        const text = aiInput.value.toLowerCase().trim();

        if (!text) {
            aiReply.innerHTML = `
                <div class="alert alert-warning">
                    Please type or speak what you want to buy.
                </div>
            `;
            return;
        }

        let query = '';

        if (text.includes('phone') || text.includes('mobile') || text.includes('camera')) {
            query = 'phone';
        } else if (text.includes('laptop') || text.includes('coding') || text.includes('study')) {
            query = 'laptop';
        } else if (text.includes('shoe') || text.includes('running')) {
            query = 'shoes';
        } else if (text.includes('watch')) {
            query = 'watch';
        } else if (text.includes('bag')) {
            query = 'bag';
        } else if (text.includes('speaker') || text.includes('earbuds') || text.includes('electronics')) {
            query = 'electronics';
        } else if (text.includes('beauty') || text.includes('face') || text.includes('skin')) {
            query = 'beauty';
        } else if (text.includes('home') || text.includes('kitchen') || text.includes('appliance')) {
            query = 'appliances';
        } else {
            query = text;
        }

        aiReply.innerHTML = `
            <div class="alert alert-info">
                AI Suggestion: Showing best products for <b>${query}</b>
            </div>
        `;

        setTimeout(function () {
            window.location.href = `/products/?q=${encodeURIComponent(query)}`;
        }, 800);
    }

    if (aiSearch) {
        aiSearch.addEventListener('click', runAISearch);
    }

    if (aiInput) {
        aiInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                runAISearch();
            }
        });
    }


    // VOICE SEARCH FOR AI

    if (aiVoiceBtn) {

        if ('webkitSpeechRecognition' in window) {

            const recognition = new webkitSpeechRecognition();

            recognition.continuous = false;
            recognition.lang = 'en-US';
            recognition.interimResults = false;

            aiVoiceBtn.addEventListener('click', function () {
                aiVoiceBtn.textContent = '🎙️ Listening...';
                recognition.start();
            });

            recognition.onresult = function (event) {
                const speechText = event.results[0][0].transcript;

                if (aiInput) {
                    aiInput.value = speechText;
                }

                aiVoiceBtn.textContent = '🎙️ Speak';
            };

            recognition.onerror = function () {
                aiVoiceBtn.textContent = '🎙️ Speak';
                alert('Voice search failed. Please try again.');
            };

            recognition.onend = function () {
                aiVoiceBtn.textContent = '🎙️ Speak';
            };

        } else {

            aiVoiceBtn.addEventListener('click', function () {
                alert('Voice search is not supported in this browser.');
            });

        }
    }


    // STAR RATING

    initStarRating();

});


// UPDATE CART ITEM

function updateCartItem(cartItemId, quantity) {

    if (!cartItemId) return;

    const formData = new FormData();

    formData.append('cart_item_id', cartItemId);
    formData.append('quantity', quantity);

    fetch('/cart/update/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {

        if (data.status === 'success') {
            location.reload();
        }

        else if (data.status === 'removed') {
            showToast('Item removed!', 'success');
            location.reload();
        }

    });
}


// UPDATE CART COUNT

function updateCartCount(count) {

    const cartCountElements = document.querySelectorAll('.cart-count');

    cartCountElements.forEach(el => {
        el.textContent = count;
    });
}


// TOAST MESSAGE

function showToast(message, type = 'info') {

    const toast = document.createElement('div');

    toast.className =
        `alert alert-${type} alert-dismissible fade show position-fixed`;

    toast.style.cssText =
        'top:20px; right:20px; z-index:9999; min-width:300px;';

    toast.innerHTML = `
        ${message}
        <button
            type="button"
            class="btn-close"
            data-bs-dismiss="alert"
        ></button>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}


// GET CSRF TOKEN

function getCSRFToken() {

    const token = document.querySelector('[name=csrfmiddlewaretoken]');

    return token ? token.value : '';
}


// STAR RATING

function initStarRating() {

    document.querySelectorAll('.star-rating input').forEach(input => {

        input.addEventListener('change', function () {

            const rating = this.value;

            const stars = this.parentNode.querySelectorAll('.star');

            stars.forEach((star, index) => {

                if (index < rating) {
                    star.classList.add('filled');
                } else {
                    star.classList.remove('filled');
                }

            });

        });

    });
}