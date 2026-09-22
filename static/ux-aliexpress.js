/**
 * AliExpress UX - Not Features - How AliExpress FEELS
 * Focus: One-thumb, dense, bottom sheet, skeleton, sticky, instant feedback
 * Family Supermarket Retreat - 063 837 8201 - FREE
 */

class AliExpressUX {
    constructor(products) {
        this.products = products || [];
        this.currentSheetProduct = null;
        this.cartCount = 0;
        this.init();
    }

    init() {
        this.injectBottomNav();
        this.injectStickySearch();
        this.injectFilterChips();
        this.injectBottomSheet();
        this.injectFloatingCart();
        this.renderDenseGrid();
        this.bindEvents();
        this.updateCartUI();
        
        // Add body class for UX mode
        document.body.classList.add('ali-ux');
        
        console.log('🛒 AliExpress UX loaded - One-thumb, dense, bottom sheet - 063 837 8201');
    }

    injectBottomNav() {
        if (document.getElementById('aliBottomNav')) return;
        
        const nav = document.createElement('nav');
        nav.id = 'aliBottomNav';
        nav.className = 'ali-bottom-nav';
        nav.innerHTML = `
            <button class="ali-bottom-nav-item active" data-nav="home">
                <span class="icon">🏠</span>
                <span>Home</span>
            </button>
            <button class="ali-bottom-nav-item" data-nav="search">
                <span class="icon">🔍</span>
                <span>Search</span>
            </button>
            <button class="ali-bottom-nav-item" data-nav="choice">
                <span class="icon">✅</span>
                <span>Choice</span>
            </button>
            <button class="ali-bottom-nav-item" data-nav="cart" id="aliNavCart">
                <span class="icon">🛒</span>
                <span>Cart</span>
            </button>
            <button class="ali-bottom-nav-item" data-nav="account">
                <span class="icon">👤</span>
                <span>Account</span>
            </button>
        `;
        document.body.appendChild(nav);
    }

    injectStickySearch() {
        const productsSection = document.getElementById('products');
        if (!productsSection || document.getElementById('aliStickySearch')) return;

        const sticky = document.createElement('div');
        sticky.id = 'aliStickySearch';
        sticky.className = 'ali-sticky-search';
        sticky.innerHTML = `
            <div class="ali-search-box">
                <span style="color:#94a3b8;">🔍</span>
                <input type="text" id="aliSearchInput" placeholder="Search rice, bread, oil... Retreat supermarket" />
                <button style="background:none;border:none;color:#94a3b8;cursor:pointer;" onclick="document.getElementById('aliSearchInput').value=''; this.closest('.ali-sticky-search').querySelector('input').dispatchEvent(new Event('input'))">✕</button>
            </div>
            <div class="ali-search-actions">
                <button class="ali-icon-btn" title="Image search" onclick="document.getElementById('image-search-ar')?.scrollIntoView({behavior:'smooth'})">📷</button>
                <button class="ali-icon-btn" title="Voice" id="aliVoiceBtn">🎤</button>
            </div>
        `;
        productsSection.prepend(sticky);
    }

    injectFilterChips() {
        const productsSection = document.getElementById('products');
        if (!productsSection || document.getElementById('aliFilterChips')) return;

        // Get categories from products
        const cats = [...new Set(this.products.map(p => p.category))].slice(0, 8);
        
        const chips = document.createElement('div');
        chips.id = 'aliFilterChips';
        chips.className = 'ali-filter-chips';
        chips.innerHTML = `
            <button class="ali-chip active" data-cat="">All</button>
            ${cats.map(c => `<button class="ali-chip" data-cat="${c}">${c}</button>`).join('')}
            <button class="ali-chip" data-cat="special" style="background:#fef3c7;border-color:#fde68a;color:#92400e;">🔥 Specials</button>
        `;
        // Insert after sticky search
        const sticky = document.getElementById('aliStickySearch');
        if (sticky) sticky.after(chips);
        else productsSection.prepend(chips);
    }

    injectBottomSheet() {
        if (document.getElementById('aliBottomSheet')) return;

        const overlay = document.createElement('div');
        overlay.id = 'aliBottomSheetOverlay';
        overlay.className = 'ali-bottom-sheet-overlay';
        overlay.onclick = () => this.closeBottomSheet();

        const sheet = document.createElement('div');
        sheet.id = 'aliBottomSheet';
        sheet.className = 'ali-bottom-sheet';
        sheet.innerHTML = `
            <div class="ali-bottom-sheet-handle"></div>
            <div id="aliSheetContent">
                <!-- Content injected dynamically -->
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(sheet);
    }

    injectFloatingCart() {
        if (document.getElementById('aliFloatingCart')) return;

        const btn = document.createElement('button');
        btn.id = 'aliFloatingCart';
        btn.className = 'ali-floating-cart';
        btn.innerHTML = `🛒<span class="ali-floating-cart-count" id="aliFloatingCount" style="display:none;">0</span>`;
        btn.onclick = () => {
            document.getElementById('cartBtn')?.click();
        };
        document.body.appendChild(btn);
    }

    renderDenseGrid() {
        const productsSection = document.getElementById('products');
        if (!productsSection) return;

        // Remove old grid if exists, create new dense grid
        let denseGrid = document.getElementById('aliDenseGrid');
        if (!denseGrid) {
            denseGrid = document.createElement('div');
            denseGrid.id = 'aliDenseGrid';
            denseGrid.className = 'ali-product-grid';
            // Insert after filter chips
            const chips = document.getElementById('aliFilterChips');
            if (chips) chips.after(denseGrid);
            else productsSection.appendChild(denseGrid);
        }

        // Show skeletons first (AliExpress progressive loading UX)
        denseGrid.innerHTML = Array(8).fill(0).map(() => `
            <div class="ali-skeleton-card">
                <div class="ali-skeleton ali-skeleton-image"></div>
                <div class="ali-skeleton ali-skeleton-text"></div>
                <div class="ali-skeleton ali-skeleton-text short"></div>
            </div>
        `).join('');

        // Render actual products after 400ms (simulate loading)
        setTimeout(() => {
            this.renderProducts(this.products);
        }, 400);
    }

    renderProducts(products) {
        const grid = document.getElementById('aliDenseGrid');
        if (!grid) return;

        if (products.length === 0) {
            grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:2rem;color:#64748b;">No products found — Try searching rice, bread, oil — 063 837 8201</div>`;
            return;
        }

        grid.innerHTML = products.map(p => {
            const isSpecial = p.special;
            const price = p.special_price || p.price;
            const oldPrice = isSpecial ? p.price : null;
            const discount = isSpecial ? Math.round((1 - price / p.price) * 100) : 0;
            const sold = Math.floor(Math.random() * 200) + 20;
            const viewing = Math.floor(Math.random() * 8) + 1;
            const rating = (4.2 + Math.random() * 0.7).toFixed(1);

            return `
                <div class="ali-product-card" onclick="window.aliUX.openBottomSheet(${p.id})" data-id="${p.id}" data-category="${p.category}">
                    <div class="ali-product-image-wrap">
                        <img src="/static/images/${p.image}" alt="${p.name}" loading="lazy" onerror="this.src='/static/images/rice.jpg'">
                        <div class="ali-product-badges">
                            ${isSpecial ? `<span class="ali-badge ali-badge-super">-${discount}%</span>` : ''}
                            ${sold > 100 ? `<span class="ali-badge ali-badge-choice">Choice</span>` : ''}
                        </div>
                        <button class="ali-product-quick-add" onclick="event.stopPropagation(); window.aliUX.quickAdd(${p.id})" title="Add to cart">+</button>
                    </div>
                    <div class="ali-product-info">
                        <div class="ali-product-title">${p.name}</div>
                        <div class="ali-product-price-row">
                            <span class="ali-price-current ${isSpecial ? 'super' : ''}">R${price}</span>
                            ${oldPrice ? `<span class="ali-price-old">R${oldPrice}</span>` : ''}
                        </div>
                        <div class="ali-product-meta">
                            <span class="ali-stars">★ ${rating}</span>
                            <span class="ali-sold">${sold} sold</span>
                        </div>
                        <div class="ali-social-proof">
                            <span class="ali-viewing"><span class="ali-viewing-dot"></span> ${viewing} viewing</span>
                            <span>• 58 5th Ave</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    openBottomSheet(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        this.currentSheetProduct = product;
        const price = product.special_price || product.price;
        const oldPrice = product.special ? product.price : null;
        const discount = product.special ? Math.round((1 - price / product.price) * 100) : 0;
        const sold = Math.floor(Math.random() * 200) + 20;
        const viewing = Math.floor(Math.random() * 8) + 2;

        const content = document.getElementById('aliSheetContent');
        if (!content) return;

        content.innerHTML = `
            <div class="ali-bottom-sheet-image">
                <img src="/static/images/${product.image}" alt="${product.name}" onerror="this.src='/static/images/rice.jpg'">
                <button onclick="window.aliUX.closeBottomSheet()" style="position:absolute;top:1rem;right:1rem;width:36px;height:36px;border-radius:50%;background:rgba(0,0,0,0.5);color:white;border:none;cursor:pointer;display:grid;place-items:center;">✕</button>
                <div style="position:absolute;bottom:1rem;left:1rem;display:flex;gap:0.5rem;">
                    ${product.special ? `<span style="background:#ff4747;color:white;padding:0.3rem 0.6rem;border-radius:20px;font-size:0.8rem;font-weight:700;">-${discount}% OFF</span>` : ''}
                    <span style="background:rgba(0,0,0,0.6);color:white;padding:0.3rem 0.6rem;border-radius:20px;font-size:0.8rem;">👀 ${viewing} viewing now</span>
                </div>
            </div>
            <div class="ali-bottom-sheet-content">
                <div style="display:flex;justify-content:space-between;align-items:start;gap:1rem;margin-bottom:0.75rem;">
                    <h3 style="font-size:1.2rem;font-weight:700;line-height:1.2;flex:1;">${product.name}</h3>
                    <button onclick="window.startAR && window.startAR({id:${product.id},name:'${product.name.replace(/'/g,"\\'")}',price:${price},image:'${product.image}',category:'${product.category}'})" style="background:#fff3cd;border:1px solid #fde68a;padding:0.4rem 0.8rem;border-radius:20px;font-size:0.8rem;cursor:pointer;">📱 AR</button>
                </div>
                
                <div style="display:flex;align-items:baseline;gap:0.5rem;margin-bottom:0.5rem;">
                    <span style="font-size:1.6rem;font-weight:800;color:${product.special ? '#ff4747' : '#0f172a'};">R${price}</span>
                    ${oldPrice ? `<span style="text-decoration:line-through;color:#94a3b8;">R${oldPrice}</span><span style="background:#ff4747;color:white;padding:0.1rem 0.4rem;border-radius:4px;font-size:0.7rem;font-weight:700;">-${discount}%</span>` : ''}
                </div>

                <div style="display:flex;gap:0.75rem;align-items:center;font-size:0.85rem;color:#64748b;margin-bottom:1rem;">
                    <span style="color:#f59e0b;">★ 4.${Math.floor(Math.random()*3)+6} (${sold} sold)</span>
                    <span>•</span>
                    <span>${product.unit} • ${product.category}</span>
                    <span>•</span>
                    <span style="color:#059669;font-weight:600;">✓ In Stock</span>
                </div>

                <div style="background:#f8fafc;border-radius:12px;padding:0.9rem;margin-bottom:1rem;">
                    <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:0.5rem;">
                        <span style="color:#64748b;">Delivery</span>
                        <span style="font-weight:600;">Free delivery for 3+ items • 58 5th Ave Retreat</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.85rem;">
                        <span style="color:#64748b;">Service</span>
                        <span style="font-weight:600;">📞 063 837 8201 • WhatsApp • 5 min reply</span>
                    </div>
                </div>

                <div style="background:#fff7ed;border:1px dashed #fed7aa;border-radius:12px;padding:0.9rem;margin-bottom:1rem;">
                    <div style="font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">🔥 Why Retreat loves this:</div>
                    <div style="font-size:0.85rem;color:#92400e;line-height:1.4;">Family-owned since 2018, cheaper than Shoprite Retreat, wholesale prices for everyone. Real product at 58 5th Ave — not dropship like AliExpress!</div>
                </div>

                <div class="ali-bottom-sheet-sticky-bar">
                    <button onclick="window.aliUX.closeBottomSheet()" style="flex:1;background:white;border:1px solid #e2e8f0;padding:0.9rem;border-radius:20px;font-weight:600;cursor:pointer;">Close</button>
                    <button onclick="window.aliUX.quickAdd(${product.id}); window.aliUX.closeBottomSheet();" style="flex:2;background:#ff4747;color:white;border:none;padding:0.9rem;border-radius:20px;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:0.5rem;">
                        <span>🛒</span> Add to Cart — R${price}
                    </button>
                </div>
            </div>
        `;

        document.getElementById('aliBottomSheetOverlay')?.classList.add('active');
        document.getElementById('aliBottomSheet')?.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeBottomSheet() {
        document.getElementById('aliBottomSheetOverlay')?.classList.remove('active');
        document.getElementById('aliBottomSheet')?.classList.remove('active');
        document.body.style.overflow = '';
        this.currentSheetProduct = null;
    }

    quickAdd(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        // Fly to cart animation like AliExpress
        const card = document.querySelector(`.ali-product-card[data-id="${productId}"]`);
        if (card) {
            const img = card.querySelector('img');
            if (img) this.flyToCart(img);
        }

        // Add to cart via existing function
        if (window.addToCartFromAI) {
            window.addToCartFromAI(product);
        } else {
            // Fallback: direct cart manipulation
            const cart = JSON.parse(localStorage.getItem('fs_cart') || '[]');
            const existing = cart.find(i => i.id === productId);
            if (existing) existing.qty = (existing.qty || 1) + 1;
            else cart.push({ id: product.id, name: product.name, price: product.special_price || product.price, image: product.image, qty: 1 });
            localStorage.setItem('fs_cart', JSON.stringify(cart));
            window.dispatchEvent(new Event('storage'));
        }

        // Update UI + feedback
        this.updateCartUI();
        this.showAddedToast(product.name);
        
        // Coins if exists
        if (window.aliCoins) window.aliCoins.addCoins(5, 'Added to cart!');
    }

    flyToCart(imgElement) {
        const rect = imgElement.getBoundingClientRect();
        const flyer = document.createElement('div');
        flyer.style.cssText = `
            position:fixed;
            left:${rect.left + rect.width/2}px;
            top:${rect.top + rect.height/2}px;
            width:40px;height:40px;
            background:url(${imgElement.src}) center/cover;
            border-radius:8px;
            z-index:9999;
            pointer-events:none;
            transition:all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow:0 4px 12px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(flyer);
        
        setTimeout(() => {
            const cartBtn = document.getElementById('aliFloatingCart') || document.getElementById('cartBtn');
            if (cartBtn) {
                const cartRect = cartBtn.getBoundingClientRect();
                flyer.style.left = cartRect.left + 'px';
                flyer.style.top = cartRect.top + 'px';
                flyer.style.width = '20px';
                flyer.style.height = '20px';
                flyer.style.opacity = '0.5';
            }
        }, 10);

        setTimeout(() => flyer.remove(), 800);
    }

    showAddedToast(name) {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position:fixed;
            bottom:90px;
            left:50%;
            transform:translateX(-50%);
            background:#0f172a;
            color:white;
            padding:0.75rem 1.25rem;
            border-radius:20px;
            font-size:0.9rem;
            z-index:3000;
            box-shadow:0 10px 30px rgba(0,0,0,0.3);
            display:flex;
            align-items:center;
            gap:0.5rem;
            animation: slideUp 0.3s ease;
        `;
        toast.innerHTML = `✅ Added ${name} to cart — 063 837 8201`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
    }

    updateCartUI() {
        try {
            const cart = JSON.parse(localStorage.getItem('fs_cart') || '[]');
            const count = cart.reduce((sum, i) => sum + (i.qty || 1), 0);
            this.cartCount = count;

            const floatingCount = document.getElementById('aliFloatingCount');
            const floatingCart = document.getElementById('aliFloatingCart');
            const navCart = document.getElementById('aliNavCart');

            if (floatingCount) {
                floatingCount.textContent = count;
                floatingCount.style.display = count > 0 ? 'grid' : 'none';
            }
            if (floatingCart) {
                if (count > 0) floatingCart.classList.add('has-items');
                else floatingCart.classList.remove('has-items');
            }
            if (navCart && count > 0) {
                navCart.innerHTML = `<span class="icon">🛒</span><span>Cart (${count})</span>`;
            }
        } catch {}
    }

    bindEvents() {
        // Search
        const searchInput = document.getElementById('aliSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const q = e.target.value.toLowerCase().trim();
                if (!q) {
                    this.renderProducts(this.products);
                    return;
                }
                const filtered = this.products.filter(p => 
                    p.name.toLowerCase().includes(q) || 
                    p.category.toLowerCase().includes(q)
                );
                this.renderProducts(filtered);
            });
        }

        // Filter chips
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('ali-chip')) {
                document.querySelectorAll('.ali-chip').forEach(c => c.classList.remove('active'));
                e.target.classList.add('active');
                
                const cat = e.target.dataset.cat;
                if (!cat) {
                    this.renderProducts(this.products);
                } else if (cat === 'special') {
                    this.renderProducts(this.products.filter(p => p.special));
                } else {
                    this.renderProducts(this.products.filter(p => p.category === cat));
                }
            }
        });

        // Bottom nav
        document.addEventListener('click', (e) => {
            const navItem = e.target.closest('.ali-bottom-nav-item');
            if (!navItem) return;
            
            document.querySelectorAll('.ali-bottom-nav-item').forEach(i => i.classList.remove('active'));
            navItem.classList.add('active');

            const nav = navItem.dataset.nav;
            if (nav === 'home') window.scrollTo({top:0, behavior:'smooth'});
            if (nav === 'search') document.getElementById('aliStickySearch')?.scrollIntoView({behavior:'smooth'});
            if (nav === 'cart') document.getElementById('cartBtn')?.click();
            if (nav === 'choice') {
                document.getElementById('choiceProgress')?.scrollIntoView({behavior:'smooth'});
                // Show choice toast
                const cart = JSON.parse(localStorage.getItem('fs_cart') || '[]');
                const count = cart.reduce((s,i)=>s+(i.qty||1),0);
                if (count >= 3) alert('✅ Choice unlocked! Free delivery — 063 837 8201');
                else alert(`Add ${3-count} more for Choice Free Delivery — like AliExpress!`);
            }
            if (nav === 'account') {
                alert('Family Supermarket Retreat\n58 5th Ave, Cape Town 7965\n📞 063 837 8201\nWhatsApp: 27638378201\nOpen: 8am-6pm Mon-Fri\nLike AliExpress account but local!');
            }
        });

        // Voice search
        document.getElementById('aliVoiceBtn')?.addEventListener('click', () => {
            if (window.voiceOrdering) window.voiceOrdering.start();
            else alert('Voice search — say \"rice\" or \"bread\" — 063 837 8201');
        });

        // Watch cart changes
        setInterval(() => this.updateCartUI(), 1000);
        window.addEventListener('storage', () => this.updateCartUI());
    }
}

console.log('🎨 AliExpress UX - One-thumb, dense, bottom sheet, skeleton - FREE - 063 837 8201');
