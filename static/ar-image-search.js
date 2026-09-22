/**
 * Image Search + AR Preview - Family Supermarket Retreat - 063 837 8201
 * TensorFlow.js MobileNet + WebXR
 */

class ImageSearchAI {
    constructor(products) {
        this.products = products || [];
        this.model = null;
        this.modelLoaded = false;
        this.loadModel();
    }

    async loadModel() {
        try {
            const status = document.getElementById('imageSearchStatus');
            if (status) status.textContent = 'Loading image recognition...';
            
            // Load TensorFlow.js
            if (!window.tf) {
                await this.loadScript('https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.10.0/dist/tf.min.js');
            }
            if (!window.mobilenet) {
                await this.loadScript('https://cdn.jsdelivr.net/npm/@tensorflow-models/mobilenet@2.1.0/dist/mobilenet.js');
            }
            
            this.model = await mobilenet.load();
            this.modelLoaded = true;
            if (status) status.textContent = 'Ready — Upload photo of bread, rice, veggies... 063 837 8201';
            console.log('ImageSearchAI ready');
        } catch (e) {
            console.log('TF load failed, using server fallback', e);
            const status = document.getElementById('imageSearchStatus');
            if (status) status.textContent = 'Ready — Upload photo (server analysis) — 063 837 8201';
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
    }

    async classifyImage(imgElement) {
        if (!this.model) return [];
        try {
            const predictions = await this.model.classify(imgElement);
            return predictions;
        } catch {
            return [];
        }
    }

    mapToProducts(predictions) {
        const keywordMap = {
            'bread': ['bakery', 'bread'],
            'baguette': ['bakery', 'bread'],
            'rice': ['staples', 'rice'],
            'oil': ['groceries', 'oil'],
            'bottle': ['drinks', 'oil'],
            'vegetable': ['produce', 'vegetables'],
            'broccoli': ['produce', 'vegetables'],
            'beverage': ['drinks'],
            'soda': ['drinks'],
            'snack': ['snacks'],
            'packet': ['snacks', 'groceries']
        };

        const matched = [];
        const seen = new Set();

        for (const pred of predictions) {
            const label = pred.className.toLowerCase();
            for (const [keyword, categories] of Object.entries(keywordMap)) {
                if (label.includes(keyword)) {
                    for (const cat of categories) {
                        for (const p of this.products) {
                            if ((p.category.toLowerCase().includes(cat) || p.name.toLowerCase().includes(keyword)) && !seen.has(p.id)) {
                                matched.push({...p, _matched: keyword});
                                seen.add(p.id);
                            }
                        }
                    }
                }
            }
        }

        return matched.slice(0, 6);
    }

    async searchByImage(file) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = async () => {
                try {
                    let products = [];
                    let predictions = [];
                    
                    if (this.modelLoaded) {
                        predictions = await this.classifyImage(img);
                        products = this.mapToProducts(predictions);
                    }
                    
                    if (products.length === 0) {
                        // Fallback to server
                        const formData = new FormData();
                        formData.append('image', file);
                        const res = await fetch('/api/image-search', {method: 'POST', body: formData});
                        const data = await res.json();
                        products = data.matched || [];
                    }
                    
                    resolve({products, predictions, fileName: file.name});
                } catch (e) {
                    reject(e);
                }
            };
            img.onerror = reject;
            img.src = URL.createObjectURL(file);
        });
    }
}

class ARPreview {
    constructor() {
        this.active = false;
        this.overlay = null;
    }

    checkSupport() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    async startAR(product) {
        if (!this.checkSupport()) {
            alert('Camera not supported on this device. Call 063 837 8201 to see product at 58 5th Ave Retreat.');
            return;
        }

        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.id = 'arOverlay';
        this.overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:black;display:flex;flex-direction:column;';
        this.overlay.innerHTML = `
            <div style="position:relative;flex:1;overflow:hidden;">
                <video id="arVideo" autoplay playsinline muted style="width:100%;height:100%;object-fit:cover;"></video>
                <div id="arProduct" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:200px;background:white;border-radius:16px;padding:1rem;box-shadow:0 10px 40px rgba(0,0,0,0.3);cursor:move;animation: float 3s ease-in-out infinite;">
                    <img src="/static/images/${product.image}" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:0.5rem;" onerror="this.src='/static/images/rice.jpg'">
                    <div style="font-weight:700;font-size:0.95rem;">${product.name}</div>
                    <div style="color:#059669;font-weight:700;">R${product.price}</div>
                    <div style="font-size:0.75rem;color:#64748b;">${product.category} • 58 5th Ave Retreat</div>
                    <div style="display:flex;gap:0.5rem;margin-top:0.75rem;">
                        <button onclick="window.addToCartFromAR && window.addToCartFromAR(${product.id})" style="flex:1;background:#0f172a;color:white;border:none;padding:0.5rem;border-radius:20px;font-weight:600;cursor:pointer;">Add to Cart</button>
                        <button onclick="window.aliUX && window.aliUX.closeBottomSheet(); document.getElementById('arOverlay')?.remove();" style="background:white;border:1px solid #e2e8f0;padding:0.5rem 0.8rem;border-radius:20px;cursor:pointer;">✕</button>
                    </div>
                    <div style="font-size:0.7rem;color:#64748b;margin-top:0.5rem;text-align:center;">Drag to move • 063 837 8201</div>
                </div>
                <button onclick="document.getElementById('arOverlay')?.remove()" style="position:absolute;top:1rem;right:1rem;width:40px;height:40px;border-radius:50%;background:rgba(0,0,0,0.6);color:white;border:none;cursor:pointer;font-size:1.2rem;">✕</button>
                <div style="position:absolute;bottom:1rem;left:1rem;right:1rem;background:rgba(0,0,0,0.7);color:white;padding:0.75rem;border-radius:12px;font-size:0.85rem;text-align:center;">
                    Point camera at table to see ${product.name} in your space<br>58 5th Ave, Retreat • 063 837 8201
                </div>
            </div>
        `;

        document.body.appendChild(this.overlay);

        try {
            const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment'}});
            const video = document.getElementById('arVideo');
            if (video) video.srcObject = stream;
            
            // Make draggable
            this.makeDraggable(document.getElementById('arProduct'));
            
            this.active = true;
        } catch (e) {
            console.log('Camera failed', e);
            // Show without camera
            const video = document.getElementById('arVideo');
            if (video) video.style.display = 'none';
            this.overlay.style.background = '#f8fafc';
        }
    }

    makeDraggable(el) {
        if (!el) return;
        let pos1=0,pos2=0,pos3=0,pos4=0;
        el.onmousedown = dragMouseDown;
        el.ontouchstart = dragTouchStart;

        function dragMouseDown(e) {
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDrag;
            document.onmousemove = elementDrag;
        }

        function dragTouchStart(e) {
            pos3 = e.touches[0].clientX;
            pos4 = e.touches[0].clientY;
            document.ontouchend = closeDrag;
            document.ontouchmove = elementTouchDrag;
        }

        function elementDrag(e) {
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            el.style.top = (el.offsetTop - pos2) + 'px';
            el.style.left = (el.offsetLeft - pos1) + 'px';
            el.style.transform = 'none';
        }

        function elementTouchDrag(e) {
            pos1 = pos3 - e.touches[0].clientX;
            pos2 = pos4 - e.touches[0].clientY;
            pos3 = e.touches[0].clientX;
            pos4 = e.touches[0].clientY;
            el.style.top = (el.offsetTop - pos2) + 'px';
            el.style.left = (el.offsetLeft - pos1) + 'px';
            el.style.transform = 'none';
        }

        function closeDrag() {
            document.onmouseup = null;
            document.onmousemove = null;
            document.ontouchend = null;
            document.ontouchmove = null;
        }
    }

    stopAR() {
        if (this.overlay) {
            const video = document.getElementById('arVideo');
            if (video && video.srcObject) {
                video.srcObject.getTracks().forEach(t => t.stop());
            }
            this.overlay.remove();
            this.overlay = null;
            this.active = false;
        }
    }
}
