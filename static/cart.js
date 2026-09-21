/* Family Supermarket - CART v4 - Smooth Motion */
let cart = JSON.parse(localStorage.getItem('fs_cart') || '[]');

const cartBtn = document.getElementById('cartBtn');
const closeCart = document.getElementById('closeCart');
const cartDrawer = document.getElementById('cartDrawer');
const cartOverlay = document.getElementById('cartOverlay');
const cartItemsEl = document.getElementById('cartItems');
const cartCountEl = document.getElementById('cartCount');
const cartItemCountEl = document.getElementById('cartItemCount');
const cartSubtotalEl = document.getElementById('cartSubtotal');
const cartTotalEl = document.getElementById('cartTotal');
const checkoutBtn = document.getElementById('checkoutBtn');
const viewCartHero = document.getElementById('viewCartHero');

function saveCart() {
    localStorage.setItem('fs_cart', JSON.stringify(cart));
    updateCartUI();
}

function updateCartUI() {
    const totalItems = cart.reduce((sum, item) => sum + item.qty, 0);
    const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);

    // Update badges
    cartCountEl.textContent = totalItems;
    cartCountEl.classList.toggle('show', totalItems > 0);
    if (cartItemCountEl) cartItemCountEl.textContent = totalItems;
    document.querySelectorAll('.cart-total-items').forEach(el => el.textContent = totalItems);

    if (cartSubtotalEl) cartSubtotalEl.textContent = `R${total.toFixed(2)}`;
    if (cartTotalEl) cartTotalEl.textContent = `R${total.toFixed(2)}`;

    // Render items
    if (cart.length === 0) {
        cartItemsEl.innerHTML = `<div id="emptyCart" style="text-align: center; padding: 3rem 1rem; color: #94a3b8;"><div style="font-size: 2.5rem; margin-bottom: 1rem;">🛒</div><h4>Your cart is empty</h4><p style="font-size: 0.9rem; margin-top: 0.5rem;">Add some fresh groceries!</p></div>`;
        if (checkoutBtn) checkoutBtn.disabled = true;
        return;
    }

    if (checkoutBtn) checkoutBtn.disabled = false;

    cartItemsEl.innerHTML = cart.map(item => `
        <div class="cart-item" data-id="${item.id}">
            <img src="/static/images/${item.image}" alt="${item.name}">
            <div style="flex: 1;">
                <div style="font-weight: 600; font-size: 0.9rem;">${item.name}</div>
                <div style="font-size: 0.8rem; color: #64748b;">R${item.price} each</div>
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
                    <button class="qty-btn" data-action="dec" data-id="${item.id}" style="width: 28px; height: 28px; border-radius: 50%; border: 1px solid #e2e8f0; background: white; cursor: pointer;">−</button>
                    <span style="font-weight: 600; min-width: 20px; text-align: center;">${item.qty}</span>
                    <button class="qty-btn" data-action="inc" data-id="${item.id}" style="width: 28px; height: 28px; border-radius: 50%; border: 1px solid #e2e8f0; background: white; cursor: pointer;">+</button>
                    <button class="remove-btn" data-id="${item.id}" style="margin-left: auto; font-size: 0.75rem; color: #ef4444; background: none; border: none; cursor: pointer;">Remove</button>
                </div>
            </div>
            <div style="font-weight: 700; font-size: 0.9rem;">R${(item.price * item.qty).toFixed(2)}</div>
        </div>
    `).join('');

    // Add qty listeners
    cartItemsEl.querySelectorAll('.qty-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = parseInt(btn.dataset.id);
            const action = btn.dataset.action;
            const item = cart.find(i => i.id === id);
            if (!item) return;
            if (action === 'inc') item.qty++;
            if (action === 'dec') item.qty = Math.max(1, item.qty - 1);
            saveCart();
        });
    });

    cartItemsEl.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            cart = cart.filter(i => i.id !== parseInt(btn.dataset.id));
            saveCart();
        });
    });
}

function openCart() {
    cartDrawer.classList.add('active');
    cartOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeCartDrawer() {
    cartDrawer.classList.remove('active');
    cartOverlay.classList.remove('active');
    document.body.style.overflow = '';
}

function addToCart(product, buttonEl) {
    // Fly animation
    if (buttonEl) {
        const rect = buttonEl.getBoundingClientRect();
        const flyer = document.createElement('div');
        flyer.className = 'fly-to-cart';
        flyer.style.left = rect.left + 'px';
        flyer.style.top = rect.top + 'px';
        document.body.appendChild(flyer);

        const cartRect = cartBtn.getBoundingClientRect();
        requestAnimationFrame(() => {
            flyer.style.left = cartRect.left + 'px';
            flyer.style.top = cartRect.top + 'px';
            flyer.style.transform = 'scale(0.2)';
            flyer.style.opacity = '0';
        });

        setTimeout(() => flyer.remove(), 800);

        // Button bounce
        buttonEl.style.transform = 'scale(0.8)';
        setTimeout(() => {
            buttonEl.style.transform = 'scale(1.2)';
            buttonEl.innerHTML = '✓';
            setTimeout(() => {
                buttonEl.style.transform = 'scale(1)';
                buttonEl.innerHTML = '+';
            }, 400);
        }, 150);
    }

    const existing = cart.find(i => i.id === product.id);
    if (existing) {
        existing.qty++;
    } else {
        cart.push({...product, qty: 1});
    }

    saveCart();

    // Haptic
    if (navigator.vibrate) navigator.vibrate(50);

    // Auto open cart on first add
    if (cart.length === 1) {
        setTimeout(openCart, 300);
    }
}

// Event listeners
cartBtn?.addEventListener('click', openCart);
closeCart?.addEventListener('click', closeCartDrawer);
cartOverlay?.addEventListener('click', closeCartDrawer);
viewCartHero?.addEventListener('click', openCart);

document.querySelectorAll('.add-to-cart').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const card = e.target.closest('.product-card');
        const product = {
            id: parseInt(card.dataset.id),
            name: card.dataset.name,
            price: parseFloat(card.dataset.price),
            image: card.dataset.image
        };
        addToCart(product, e.target);
    });
});

// Checkout
checkoutBtn?.addEventListener('click', async () => {
    const name = document.getElementById('customerName')?.value || 'Guest';
    const phone = document.getElementById('customerPhone')?.value || '';
    const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);

    if (cart.length === 0) return;

    checkoutBtn.innerHTML = '<span>⏳ Processing...</span>';
    checkoutBtn.disabled = true;

    try {
        const res = await fetch('/api/checkout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({items: cart, total, name, phone})
        });

        const data = await res.json();

        if (data.success) {
            // Open WhatsApp
            window.open(data.whatsapp_url, '_blank');

            // Clear cart
            cart = [];
            saveCart();
            closeCartDrawer();

            // Show success
            setTimeout(() => {
                alert(`✅ Order ${data.order_id} placed! WhatsApp opened. We'll confirm in 5 mins.`);
            }, 500);
        }
    } catch (err) {
        console.error(err);
        // Fallback: direct WhatsApp
        let text = `Hi Family Supermarket! Order from ${name}:\n`;
        cart.forEach(item => {
            text += `- ${item.name} x${item.qty} = R${(item.price * item.qty).toFixed(2)}\n`;
        });
        text += `\nTotal: R${total.toFixed(2)}\nPhone: ${phone}`;
        window.open(`https://wa.me/27796232189?text=${encodeURIComponent(text)}`, '_blank');
    }

    checkoutBtn.innerHTML = '<span>Checkout via WhatsApp →</span>';
    checkoutBtn.disabled = false;
});

// Init
updateCartUI();

console.log('🛒 Cart v4 loaded - Smooth motion + WhatsApp checkout');
