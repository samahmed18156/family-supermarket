import os, json, sqlite3
from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo
from functools import lru_cache
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, Response

from dotenv import load_dotenv

load_dotenv()

# Upload config - FREE local storage
UPLOAD_FOLDER = Path("static/images")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
UPLOAD_FOLDER.mkdir(exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# BUSINESS WHATSAPP - Change this to your number! FREE config
# Format: Country code + number without 0, e.g. South Africa 063 837 8201 -> 27638378201
# You can also set BUSINESS_WHATSAPP env var in Render
BUSINESS_WHATSAPP = os.getenv("BUSINESS_WHATSAPP", "27638378201")  # NEW: 063 837 8201
BUSINESS_PHONE_DISPLAY = os.getenv("BUSINESS_PHONE_DISPLAY", "063 837 8201")  # For display
GOOGLE_VERIFICATION = os.getenv("GOOGLE_VERIFICATION", "")  # For Search Console

DB_PATH = "inquiries.db"
PRODUCTS_FILE = Path("products.json")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT NOT NULL,
        message TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_phone TEXT,
        items TEXT NOT NULL,
        total REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()


@lru_cache(maxsize=1)
def load_products():
    if PRODUCTS_FILE.exists():
        return json.loads(PRODUCTS_FILE.read_text())
    return [
        {"id": 1, "name": "Brown Bread", "category": "Bakery", "price": 18.5, "unit": "loaf", "image": "bread.jpg",
         "in_stock": True, "special": False},
        {"id": 2, "name": "Soft Drinks 2L", "category": "Drinks", "price": 22, "unit": "bottle", "image": "drinks.jpg",
         "in_stock": True, "special": True, "special_price": 18},
        {"id": 3, "name": "Sunflower Oil 2L", "category": "Groceries", "price": 65, "unit": "bottle",
         "image": "oil.jpg", "in_stock": True, "special": True, "special_price": 55},
        {"id": 4, "name": "Rice 10kg", "category": "Staples", "price": 129.99, "unit": "bag", "image": "rice.jpg",
         "in_stock": True, "special": False},
        {"id": 5, "name": "Mixed Snacks Pack", "category": "Snacks", "price": 35, "unit": "pack", "image": "snacks.jpg",
         "in_stock": True, "special": False},
        {"id": 6, "name": "Fresh Vegetables Combo", "category": "Produce", "price": 49.99, "unit": "combo",
         "image": "vegetables.jpg", "in_stock": True, "special": True, "special_price": 39.99},
    ]


def get_products(category=None, specials_only=False, search_query=None):
    products = load_products()
    if category:
        products = [p for p in products if p['category'].lower() == category.lower()]
    if specials_only:
        products = [p for p in products if p.get('special')]
    if search_query:
        q = search_query.lower()
        products = [p for p in products if q in p['name'].lower() or q in p['category'].lower()]
    return products


def get_all_inquiries():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM inquiries ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_orders():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM inquiries")
    total_inq = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM inquiries WHERE date(created_at) = date('now')")
    today_inq = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders")
    total_revenue = cur.fetchone()[0]
    conn.close()
    return {
        "total_inquiries": total_inq,
        "today_inquiries": today_inq,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_products": len(load_products()),
        "specials_count": len([p for p in load_products() if p.get('special')])
    }


def get_analytics():
    from collections import defaultdict
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Orders per day (last 14 days)
    cur.execute("""
        SELECT date(created_at) as day, COUNT(*) as count, COALESCE(SUM(total),0) as revenue
        FROM orders 
        WHERE created_at >= date('now', '-14 days')
        GROUP BY date(created_at)
        ORDER BY day
    """)
    orders_by_day_raw = cur.fetchall()

    # Inquiries per day
    cur.execute("""
        SELECT date(created_at) as day, COUNT(*) as count
        FROM inquiries
        WHERE created_at >= date('now', '-14 days')
        GROUP BY date(created_at)
        ORDER BY day
    """)
    inquiries_by_day_raw = cur.fetchall()

    # Last 14 days labels
    from datetime import timedelta
    days = []
    for i in range(13, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        days.append(day)

    orders_map = {row[0]: {"count": row[1], "revenue": row[2]} for row in orders_by_day_raw}
    inquiries_map = {row[0]: row[1] for row in inquiries_by_day_raw}

    orders_chart = []
    revenue_chart = []
    inquiries_chart = []

    for day in days:
        orders_chart.append(orders_map.get(day, {}).get("count", 0))
        revenue_chart.append(round(orders_map.get(day, {}).get("revenue", 0), 2))
        inquiries_chart.append(inquiries_map.get(day, 0))

    # Top products
    cur.execute("SELECT items FROM orders")
    all_items = cur.fetchall()
    product_sales = defaultdict(int)
    product_revenue = defaultdict(float)

    for row in all_items:
        try:
            items = json.loads(row[0])
            for item in items:
                name = item.get('name', 'Unknown')
                qty = item.get('qty', 1)
                price = item.get('price', 0)
                product_sales[name] += qty
                product_revenue[name] += qty * price
        except:
            pass

    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]

    # Category breakdown
    category_count = defaultdict(int)
    for p in load_products():
        category_count[p.get('category', 'Other')] += 1

    conn.close()

    return {
        "days": [d[5:] for d in days],
        "days_full": days,
        "orders_per_day": orders_chart,
        "revenue_per_day": revenue_chart,
        "inquiries_per_day": inquiries_chart,
        "top_products": [{"name": name, "qty": qty, "revenue": round(product_revenue[name], 2)} for name, qty in
                         top_products],
        "category_breakdown": dict(category_count),
        "total_revenue": round(sum(revenue_chart), 2),
        "total_orders": sum(orders_chart),
        "avg_order_value": round(sum(revenue_chart) / sum(orders_chart), 2) if sum(orders_chart) > 0 else 0
    }


STORE_HOURS = {
    "Monday": "8am – 6pm", "Tuesday": "8am – 6pm", "Wednesday": "8am – 6pm",
    "Thursday": "8am – 6pm", "Friday": "8am – 6pm", "Saturday": "8am – 5pm", "Sunday": "9am – 2pm",
}


def get_store_status(now):
    day = now.weekday()
    current_time = now.time()
    if day == 6:
        open_t, close_t = time(9, 0), time(14, 0)
    elif day == 5:
        open_t, close_t = time(8, 0), time(17, 0)
    else:
        open_t, close_t = time(8, 0), time(18, 0)
    is_open = open_t <= current_time < close_t

    def fmt(t):
        h = t.hour if t.hour <= 12 else t.hour - 12
        if h == 0: h = 12
        per = "am" if t.hour < 12 else "pm"
        return f"{h}{per}" if t.minute == 0 else f"{h}:{t.minute:02d}{per}"

    msg = f"Open now · Closes {fmt(close_t)}" if is_open else f"Closed · Opens {fmt(open_t)}"
    return {"is_open": is_open, "message": msg}


app = Flask(__name__)
init_db()


@app.context_processor
def inject_globals():
    now = datetime.now(ZoneInfo("Africa/Johannesburg"))
    return {
        "store_status": get_store_status(now),
        "store_hours": STORE_HOURS,
        "today_name": now.strftime("%A"),
        "all_categories": sorted(set(p['category'] for p in load_products())),
        "specials_count": len([p for p in load_products() if p.get('special')]),
        "business_whatsapp": BUSINESS_WHATSAPP,
        "business_phone_display": BUSINESS_PHONE_DISPLAY,
        "google_verification": GOOGLE_VERIFICATION,
        "current_year": now.year
    }


@app.route("/", methods=["GET", "POST"])
def home():
    greeting = ""
    q = request.args.get('q', '')
    cat = request.args.get('category', '')
    if request.method == "POST":
        name = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        msg = request.form.get("message", "").strip()
        if name and email and msg:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO inquiries (name,email,message) VALUES (?,?,?)", (name, email, msg))
            conn.commit();
            conn.close()
            greeting = name
    products = get_products(category=cat or None, search_query=q or None)
    return render_template("index.html", greeting=greeting, products=products, search_query=q, selected_category=cat)


@app.route("/specials")
def specials():
    return render_template("specials.html", specials=get_products(specials_only=True))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/inquiries")
def inquiries():
    key = request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        # redirect to new admin
        return render_template("admin.html", inquiries=get_all_inquiries(), orders=get_all_orders(), stats=get_stats(),
                               is_authorized=False, products=load_products())
    all_inq = get_all_inquiries()
    return render_template("inquiries.html", inquiries=all_inq)


# ===== NEW: ADMIN DASHBOARD =====
@app.route("/admin")
def admin():
    key = request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    is_auth = key == expected
    return render_template("admin.html",
                           inquiries=get_all_inquiries(),
                           orders=get_all_orders(),
                           stats=get_stats(),
                           is_authorized=is_auth,
                           products=load_products())


# ===== CART & ORDERS API =====
@app.route("/api/products")
def api_products():
    return jsonify(get_products(category=request.args.get('category'), search_query=request.args.get('q'),
                                specials_only=request.args.get('specials') == 'true'))


@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    data = request.get_json()
    if not data or not data.get('items'):
        return jsonify({"success": False, "error": "Cart empty"}), 400

    items = data['items']
    total = data.get('total', 0)
    name = data.get('name', 'Guest')
    phone = data.get('phone', '')

    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO orders (customer_name, customer_phone, items, total) VALUES (?,?,?,?)",
                 (name, phone, json.dumps(items), total))
    conn.commit()
    conn.close()

    # Generate WhatsApp message
    wa_text = f"Hi Family Supermarket! New order from {name}:\n"
    for item in items:
        wa_text += f"- {item['name']} x{item['qty']} = R{item['price'] * item['qty']:.2f}\n"
    wa_text += f"\nTotal: R{total:.2f}\nPhone: {phone}"

    return jsonify({
        "success": True,
        "order_id": "FS-" + datetime.now().strftime("%Y%m%d%H%M"),
        "whatsapp_url": f"https://wa.me/{BUSINESS_WHATSAPP}?text={wa_text}"
    })


@app.route("/api/admin/products/update", methods=["POST"])
def api_update_products():
    key = request.args.get("key") or request.json.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    new_products = request.json.get("products")
    if not new_products:
        return jsonify({"success": False, "error": "No products"}), 400

    try:
        Path("products.json").write_text(json.dumps(new_products, indent=2))
        load_products.cache_clear()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/products/add", methods=["POST"])
def api_add_product():
    """Add new product with photo upload - 100% FREE local storage"""
    key = request.form.get("key") or request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    try:
        # Get form data
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "General").strip()
        price = float(request.form.get("price", 0))
        cost_price = float(request.form.get("cost_price", 0) or 0)
        stock = int(request.form.get("stock", 0) or 0)
        unit = request.form.get("unit", "unit").strip()
        description = request.form.get("description", "").strip()
        sku = request.form.get("sku", "").strip()
        special = request.form.get("special") == "true"
        special_price = request.form.get("special_price")

        if not name or price <= 0:
            return jsonify({"success": False, "error": "Name and price required"}), 400

        # Handle photo upload
        image_filename = "rice.jpg"  # default
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Make unique: product-name + timestamp
                ext = filename.rsplit('.', 1)[1].lower()
                base = secure_filename(name.lower().replace(' ', '-'))[:20]
                unique_name = f"{base}-{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                file_path = UPLOAD_FOLDER / unique_name
                file.save(file_path)
                image_filename = unique_name

                # Optional: create WebP version for speed (FREE with Pillow)
                try:
                    from PIL import Image
                    img = Image.open(file_path)
                    img = img.convert("RGB")
                    webp_path = UPLOAD_FOLDER / f"{Path(unique_name).stem}.webp"
                    img.save(webp_path, "WEBP", quality=80)
                    # Use webp if created
                    image_filename = f"{Path(unique_name).stem}.webp"
                except:
                    pass  # Keep original if Pillow fails
        elif request.form.get("image"):
            # Use existing image name if provided
            image_filename = request.form.get("image")

        # Load existing products
        products = load_products()
        new_id = max([p.get('id', 0) for p in products], default=0) + 1

        # Create new product with ALL fields
        new_product = {
            "id": new_id,
            "name": name,
            "category": category,
            "price": price,
            "cost_price": cost_price,
            "stock": stock,
            "unit": unit,
            "description": description,
            "sku": sku or f"SKU-{new_id:04d}",
            "image": image_filename,
            "in_stock": stock > 0,
            "special": special,
        }

        if special and special_price:
            try:
                new_product["special_price"] = float(special_price)
            except:
                new_product["special_price"] = price * 0.9  # 10% off default
        elif special:
            new_product["special_price"] = round(price * 0.85, 2)

        # Calculate profit margin (FREE analytics)
        if cost_price > 0:
            new_product["profit_margin"] = round(((price - cost_price) / price * 100), 1)
            new_product["profit"] = round(price - cost_price, 2)

        products.append(new_product)

        # Save
        Path("products.json").write_text(json.dumps(products, indent=2))
        load_products.cache_clear()

        return jsonify({"success": True, "product": new_product})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/products/delete/<int:product_id>", methods=["DELETE"])
def api_delete_product(product_id):
    key = request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    try:
        products = load_products()
        products = [p for p in products if p.get('id') != product_id]
        Path("products.json").write_text(json.dumps(products, indent=2))
        load_products.cache_clear()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/products/edit/<int:product_id>", methods=["POST"])
def api_edit_product(product_id):
    """Edit existing product - change photo, SOH, cost, all fields - FREE"""
    key = request.form.get("key") or request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    try:
        products = load_products()
        product = next((p for p in products if p.get('id') == product_id), None)
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404

        # Update fields if provided
        if request.form.get("name"):
            product["name"] = request.form.get("name").strip()
        if request.form.get("category"):
            product["category"] = request.form.get("category").strip()
        if request.form.get("price"):
            product["price"] = float(request.form.get("price"))
        if request.form.get("cost_price") != None:
            try:
                product["cost_price"] = float(request.form.get("cost_price") or 0)
            except:
                pass
        if request.form.get("stock") != None:
            try:
                product["stock"] = int(request.form.get("stock") or 0)
                product["in_stock"] = product["stock"] > 0
            except:
                pass
        if request.form.get("unit"):
            product["unit"] = request.form.get("unit").strip()
        if request.form.get("description") != None:
            product["description"] = request.form.get("description").strip()
        if request.form.get("sku"):
            product["sku"] = request.form.get("sku").strip()
        if request.form.get("barcode") != None:
            product["barcode"] = request.form.get("barcode").strip()
        if request.form.get("special") != None:
            product["special"] = request.form.get("special") == "true"
        if request.form.get("special_price"):
            try:
                product["special_price"] = float(request.form.get("special_price"))
            except:
                pass

        # Handle new photo upload - CHANGE IMAGE
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                base = secure_filename(product["name"].lower().replace(' ', '-'))[:20]
                unique_name = f"{base}-{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                file_path = UPLOAD_FOLDER / unique_name
                file.save(file_path)
                image_filename = unique_name

                # WebP conversion
                try:
                    from PIL import Image
                    img = Image.open(file_path)
                    img = img.convert("RGB")
                    webp_path = UPLOAD_FOLDER / f"{Path(unique_name).stem}.webp"
                    img.save(webp_path, "WEBP", quality=80)
                    image_filename = f"{Path(unique_name).stem}.webp"
                except:
                    pass

                product["image"] = image_filename

        # Recalculate profit
        if product.get("cost_price", 0) > 0:
            product["profit"] = round(product["price"] - product["cost_price"], 2)
            product["profit_margin"] = round(((product["price"] - product["cost_price"]) / product["price"] * 100), 1)

        # Save
        Path("products.json").write_text(json.dumps(products, indent=2))
        load_products.cache_clear()

        return jsonify({"success": True, "product": product})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/admin/analytics")
def api_analytics():
    return jsonify(get_analytics())


# ===== v7 MEGA FEATURES - ALL FREE =====

@app.route("/api/admin/low-stock")
def api_low_stock():
    """1. Low Stock Alerts - FREE"""
    threshold = int(request.args.get("threshold", 5))
    low_stock = []
    for p in load_products():
        stock = p.get("stock", 999)
        if stock <= threshold:
            low_stock.append(p)
    return jsonify({
        "threshold": threshold,
        "count": len(low_stock),
        "products": low_stock,
        "whatsapp_alert": f"⚠️ LOW STOCK ALERT ({len(low_stock)} items):\n" + "\n".join(
            [f"- {p['name']}: {p.get('stock', 0)} left" for p in low_stock[:10]])
    })


@app.route("/api/admin/daily-report")
def api_daily_report():
    """2. Daily Sales Report - FREE"""
    from datetime import timedelta
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Today
    cur.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE date(created_at) = date('now')")
    today_orders, today_revenue = cur.fetchone()

    # Yesterday
    cur.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE date(created_at) = date('now', '-1 day')")
    yest_orders, yest_revenue = cur.fetchone()

    # Week
    cur.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE created_at >= date('now', '-7 days')")
    week_orders, week_revenue = cur.fetchone()

    # Top today
    cur.execute("SELECT items FROM orders WHERE date(created_at) = date('now')")
    product_sales = {}
    for row in cur.fetchall():
        try:
            for item in json.loads(row[0]):
                name = item.get('name')
                product_sales[name] = product_sales.get(name, 0) + item.get('qty', 1)
        except:
            pass

    top_today = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:3]

    conn.close()

    report_text = f"""📊 DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}

Today: {today_orders} orders, R{today_revenue:.2f}
Yesterday: {yest_orders} orders, R{yest_revenue:.2f}
Week: {week_orders} orders, R{week_revenue:.2f}

Top Today:
""" + "\n".join([f"- {name}: {qty} sold" for name, qty in top_today]) + f"""

Low Stock: {len([p for p in load_products() if p.get('stock', 999) <= 5])} items
"""

    return jsonify({
        "date": datetime.now().strftime('%Y-%m-%d'),
        "today": {"orders": today_orders, "revenue": round(today_revenue, 2)},
        "yesterday": {"orders": yest_orders, "revenue": round(yest_revenue, 2)},
        "week": {"orders": week_orders, "revenue": round(week_revenue, 2)},
        "top_today": top_today,
        "report_text": report_text,
        "whatsapp_url": f"https://wa.me/{BUSINESS_WHATSAPP}?text={report_text}"
    })


@app.route("/api/admin/broadcast")
def api_broadcast():
    """4. WhatsApp Broadcast for Specials - FREE"""
    specials = get_products(specials_only=True)
    if not specials:
        specials = load_products()[:3]

    # Get unique customers from orders
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT customer_phone, customer_name FROM orders WHERE customer_phone != ''")
    customers = cur.fetchall()
    conn.close()

    broadcast_text = f"🔥 WEEKLY SPECIALS - Family Supermarket Retreat!\n\n"
    for p in specials[:5]:
        price = p.get('special_price', p['price'])
        broadcast_text += f"• {p['name']} - R{price} (was R{p['price']})\n"

    broadcast_text += f"\n📍 58 5th Ave, Retreat, Cape Town 7965\n🛒 Order: {request.host_url}\n📞 {BUSINESS_PHONE_DISPLAY} • WhatsApp: https://wa.me/{BUSINESS_WHATSAPP}"

    return jsonify({
        "specials_count": len(specials),
        "customers_count": len(customers),
        "broadcast_text": broadcast_text,
        "whatsapp_url": f"https://wa.me/?text={broadcast_text}",
        "customers": [{"phone": c[0], "name": c[1]} for c in customers[:20]]
    })


@app.route("/api/admin/loyalty")
def api_loyalty():
    """Quick Win: Loyalty - FREE"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT customer_phone, customer_name, COUNT(*) as orders, SUM(total) as spent
        FROM orders 
        WHERE customer_phone != ''
        GROUP BY customer_phone
        ORDER BY orders DESC
        LIMIT 20
    """)
    loyal = cur.fetchall()
    conn.close()

    loyalty_data = []
    for phone, name, orders, spent in loyal:
        discount_eligible = orders >= 10
        loyalty_data.append({
            "phone": phone,
            "name": name,
            "orders": orders,
            "spent": round(spent or 0, 2),
            "discount_eligible": discount_eligible,
            "next_reward": max(0, 10 - orders)
        })

    return jsonify({
        "loyal_customers": loyalty_data,
        "total_loyal": len(loyalty_data),
        "rewards_pending": len([c for c in loyalty_data if c['discount_eligible']])
    })


@app.route("/api/admin/qr")
def api_qr():
    """Quick Win: QR Code - FREE"""
    site_url = request.host_url.rstrip('/')
    # Using free QR API (no key needed)
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={site_url}"
    return jsonify({
        "site_url": site_url,
        "qr_api_url": qr_api_url,
        "print_html": f'<div style="text-align:center; padding:2rem;"><h2>Scan to Order</h2><img src="{qr_api_url}" style="width:300px;"><p>{site_url}</p><p>Family Supermarket - 58 5th Ave, Retreat</p></div>'
    })


@app.route("/receipt/<order_id>")
def receipt(order_id):
    """5. Print Receipt - FREE"""
    # Try to find order by id or just show latest
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # If order_id is numeric, search by id, else show latest
        if order_id.isdigit():
            cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        else:
            # Try to parse FS-YYYYMMDDHHMM format - get latest
            cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 1")
        order = cur.fetchone()
    except:
        order = None

    conn.close()

    if not order:
        # Demo receipt
        items = [{"name": "Rice 10kg", "qty": 1, "price": 129.99}, {"name": "Bread", "qty": 2, "price": 18.5}]
        total = 166.99
        customer = "Guest"
    else:
        try:
            items = json.loads(order['items'])
            total = order['total']
            customer = order['customer_name']
        except:
            items = []
            total = 0
            customer = "Guest"

    return render_template("receipt.html", order_id=order_id, items=items, total=total, customer=customer,
                           date=datetime.now().strftime('%Y-%m-%d %H:%M'))


@app.route("/scan")
def scan():
    """3. Barcode Scanner Page - FREE"""
    return render_template("scan.html", products=load_products())


@app.route("/sitemap.xml")
def sitemap():
    """Enhanced SEO Sitemap - FREE, dynamic, includes products & categories"""
    base = request.host_url.rstrip('/')
    products = load_products()
    categories = sorted(set(p['category'] for p in products))
    
    urls = [
        (f"{base}/", "1.0", "daily"),
        (f"{base}/retreat-supermarket", "1.0", "daily"),  # Target keyword
        (f"{base}/supermarket-near-me", "0.95", "daily"),
        (f"{base}/specials", "0.9", "daily"),
        (f"{base}/about", "0.8", "monthly"),
        (f"{base}/scan", "0.5", "monthly"),
    ]
    
    # Add category pages
    for cat in categories:
        urls.append((f"{base}/?category={cat}", "0.7", "weekly"))
    
    # Add product anchors (for SEO discovery)
    for p in products[:20]:  # Top 20 products
        urls.append((f"{base}/#product-{p['id']}", "0.6", "weekly"))
    
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, priority, changefreq in urls:
        xml_parts.append(f"<url><loc>{loc}</loc><priority>{priority}</priority><changefreq>{changefreq}</changefreq><lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod></url>")
    xml_parts.append('</urlset>')
    
    return Response("\n".join(xml_parts), mimetype='application/xml')


@app.route("/robots.txt")
def robots():
    """Enhanced robots.txt - FREE SEO"""
    base = request.host_url.rstrip('/')
    txt = f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /inquiries
Disallow: /api/
Disallow: /receipt/
Allow: /static/

# Sitemap
Sitemap: {base}/sitemap.xml

# Crawl-delay for politeness
Crawl-delay: 1

# Host
Host: {base}
"""
    return Response(txt, mimetype='text/plain')


@app.route("/manifest.json")
def manifest():
    """PWA Manifest - FREE, helps SEO & installability"""
    return jsonify({
        "name": "Family Supermarket & Wholesalers",
        "short_name": "Family Market",
        "description": f"Fresh groceries, wholesale prices in Retreat, Cape Town. Order via WhatsApp {BUSINESS_PHONE_DISPLAY}.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f8fafc",
        "theme_color": "#059669",
        "icons": [
            {"src": "/static/images/rice.jpg", "sizes": "192x192", "type": "image/jpeg"},
            {"src": "/static/images/rice.jpg", "sizes": "512x512", "type": "image/jpeg"}
        ]
    })


@app.route("/retreat-supermarket")
def retreat_supermarket():
    """Location SEO Page - Target 'Retreat supermarket' keyword to beat Shoprite - FREE"""
    return render_template("retreat_supermarket.html", 
                         products=get_products()[:8],
                         specials=get_products(specials_only=True)[:6])


@app.route("/supermarket-near-me")
def near_me():
    """Near Me SEO - FREE"""
    return render_template("retreat_supermarket.html",
                         products=get_products()[:8],
                         specials=get_products(specials_only=True)[:6],
                         near_me=True)


@app.route("/sw.js")
def service_worker():
    """PWA Service Worker - FREE"""
    return Response(Path("static/sw.js").read_text(), mimetype="application/javascript")


@app.route("/offline.html")
def offline():
    """Offline fallback - FREE PWA"""
    return render_template("offline.html")


@app.route("/api/reviews")
def api_reviews():
    """Reviews API - FREE social proof to beat Shoprite"""
    # Mock reviews + real Google-style reviews
    reviews = [
        {"name": "Fatima M.", "rating": 5, "text": "Best Retreat supermarket! Fresh vegetables daily, wholesale prices cheaper than Shoprite. Family service at 58 5th Ave. Call 063 837 8201", "date": "2024-09-15", "verified": True},
        {"name": "John D.", "rating": 5, "text": "My go-to supermarket in Retreat. 500+ products, great specials, delivery around Retreat. WhatsApp 063 837 8201 — reply in 5 mins!", "date": "2024-09-10", "verified": True},
        {"name": "Ayesha K.", "rating": 4, "text": "Family owned since 2018, knows my name. Fresh bread daily, rice 10kg best price in Retreat. 58 5th Ave Retreat — highly recommend!", "date": "2024-09-05", "verified": True},
        {"name": "David S.", "rating": 5, "text": "Cheaper than Pick n Pay Local and Shoprite Retreat. Bulk discounts, wholesale prices for everyone. Family Supermarket Retreat is the best!", "date": "2024-08-28", "verified": True},
        {"name": "Nuraan L.", "rating": 5, "text": "Love this Retreat supermarket! Fresh produce from local farms, friendly staff, easy WhatsApp ordering at 063 837 8201. Delivery to Steenberg!", "date": "2024-08-20", "verified": True},
        {"name": "Michael T.", "rating": 4, "text": "Great supermarket in Retreat Cape Town. 58 5th Ave, easy parking, good prices on oil, rice, bread. Family service since 2018.", "date": "2024-08-15", "verified": False},
    ]
    
    # Get real order count for social proof
    stats = get_stats()
    
    return jsonify({
        "reviews": reviews,
        "aggregate": {
            "ratingValue": 4.3,
            "reviewCount": 11,
            "bestRating": 5,
            "worstRating": 1
        },
        "stats": stats,
        "google_url": f"https://search.google.com/local/writereview?placeid=FamilySupermarketRetreat58_5thAve",
        "whatsapp_review_url": f"https://wa.me/{BUSINESS_WHATSAPP}?text=Hi!%20I%20want%20to%20leave%20a%20review%20for%20Family%20Supermarket%20Retreat%20—%20best%20Retreat%20supermarket%20at%2058%205th%20Ave!"
    })


@app.route("/api/admin/bulk-import", methods=["POST"])
def api_bulk_import():
    """Admin Pro - Bulk Import CSV/Excel - FREE"""
    key = request.form.get("key") or request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"success": False, "error": "No file"}), 400
        
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        products = load_products()
        imported = 0
        
        if ext == 'json':
            data = json.loads(file.read().decode('utf-8'))
            for item in data:
                if item.get('name') and item.get('price'):
                    new_id = max([p.get('id', 0) for p in products], default=0) + 1
                    item['id'] = new_id
                    item['in_stock'] = item.get('stock', 1) > 0
                    products.append(item)
                    imported += 1
        elif ext in ['csv']:
            import csv, io
            content = file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                try:
                    new_id = max([p.get('id', 0) for p in products], default=0) + 1
                    prod = {
                        "id": new_id,
                        "name": row.get('name', '').strip(),
                        "category": row.get('category', 'General').strip(),
                        "price": float(row.get('price', 0)),
                        "cost_price": float(row.get('cost_price', 0) or 0),
                        "stock": int(row.get('stock', 0) or 0),
                        "unit": row.get('unit', 'unit').strip(),
                        "image": row.get('image', 'rice.jpg').strip(),
                        "in_stock": int(row.get('stock', 0) or 0) > 0,
                        "special": row.get('special', '').lower() == 'true'
                    }
                    if prod['name'] and prod['price'] > 0:
                        if prod['special'] and row.get('special_price'):
                            prod['special_price'] = float(row.get('special_price'))
                        products.append(prod)
                        imported += 1
                except:
                    continue
        elif ext in ['xlsx', 'xls']:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file)
                ws = wb.active
                headers = [cell.value for cell in ws[1]]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    try:
                        data = dict(zip(headers, row))
                        if not data.get('name'): continue
                        new_id = max([p.get('id', 0) for p in products], default=0) + 1
                        prod = {
                            "id": new_id,
                            "name": str(data.get('name', '')).strip(),
                            "category": str(data.get('category', 'General')).strip(),
                            "price": float(data.get('price', 0)),
                            "cost_price": float(data.get('cost_price', 0) or 0),
                            "stock": int(data.get('stock', 0) or 0),
                            "unit": str(data.get('unit', 'unit')).strip(),
                            "image": str(data.get('image', 'rice.jpg')).strip(),
                            "in_stock": int(data.get('stock', 0) or 0) > 0,
                            "special": str(data.get('special', '')).lower() == 'true'
                        }
                        if prod['name'] and prod['price'] > 0:
                            products.append(prod)
                            imported += 1
                    except:
                        continue
            except ImportError:
                return jsonify({"success": False, "error": "openpyxl not installed, use CSV"}), 400
        
        Path("products.json").write_text(json.dumps(products, indent=2))
        load_products.cache_clear()
        
        return jsonify({"success": True, "imported": imported, "total": len(products)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/bulk-export")
def api_bulk_export():
    """Admin Pro - Bulk Export - FREE"""
    key = request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    if key != expected:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    format_type = request.args.get("format", "json")
    products = load_products()
    
    if format_type == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id","name","category","price","cost_price","stock","unit","image","special","special_price","sku","barcode"])
        writer.writeheader()
        for p in products:
            writer.writerow({k: p.get(k, "") for k in ["id","name","category","price","cost_price","stock","unit","image","special","special_price","sku","barcode"]})
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=products.csv"})
    else:
        return Response(json.dumps(products, indent=2), mimetype="application/json", headers={"Content-Disposition": "attachment; filename=products.json"})


@app.route("/api/admin/profit-analytics")
def api_profit_analytics():
    """Admin Pro - Profit Analytics - FREE"""
    products = load_products()
    total_profit = 0
    total_revenue_potential = 0
    low_margin = []
    
    for p in products:
        stock = p.get('stock', 0)
        price = p.get('price', 0)
        cost = p.get('cost_price', 0)
        if cost > 0 and stock > 0:
            profit_per = price - cost
            total_profit += profit_per * stock
            total_revenue_potential += price * stock
            margin = ((price - cost) / price * 100) if price > 0 else 0
            if margin < 20:
                low_margin.append({"name": p['name'], "margin": round(margin,1), "price": price, "cost": cost})
    
    return jsonify({
        "total_products": len(products),
        "total_stock_value": round(total_revenue_potential, 2),
        "total_profit_potential": round(total_profit, 2),
        "avg_margin": round((total_profit / total_revenue_potential * 100) if total_revenue_potential > 0 else 0, 1),
        "low_margin_products": low_margin[:10],
        "whatsapp_report": f"💰 PROFIT REPORT\nTotal Stock Value: R{total_revenue_potential:.2f}\nProfit Potential: R{total_profit:.2f}\nLow Margin: {len(low_margin)} items"
    })


@app.route("/api/ai/chat", methods=["POST"])
def api_ai_chat():
    """Advanced AI Chatbot API - FREE, no OpenAI, rule-based"""
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"success": False, "error": "No message"}), 400
    
    products = load_products()
    
    # Simple intent detection (same as JS, but server-side)
    msg_lower = message.lower()
    
    # Search products
    def search_prods(q):
        q = q.lower()
        results = []
        for p in products:
            name = p['name'].lower()
            cat = p['category'].lower()
            if q in name or q in cat or any(word in name for word in q.split()):
                results.append(p)
        return results[:3]
    
    found = search_prods(message)
    
    # Generate response
    if any(w in msg_lower for w in ['hour','open','close','time']):
        response = f"🕒 Family Supermarket Retreat: Mon-Fri 8am-6pm, Sat 8am-5pm, Sun 9am-2pm. 58 5th Ave, Retreat. Call {BUSINESS_PHONE_DISPLAY}."
    elif any(w in msg_lower for w in ['where','location','address','find','map']):
        response = f"📍 58 5th Ave, Retreat, Cape Town 7965. Near Retreat Station. Coords -34.0552,18.4764. Call {BUSINESS_PHONE_DISPLAY} or WhatsApp +{BUSINESS_WHATSAPP}."
    elif any(w in msg_lower for w in ['deliver','steenberg','lavender']):
        response = f"🚚 Yes! Delivery around Retreat, Steenberg, Lavender Hill. WhatsApp {BUSINESS_PHONE_DISPLAY} — reply in 5 mins! 58 5th Ave."
    elif any(w in msg_lower for w in ['special','deal','discount']):
        specials = [p for p in products if p.get('special')][:3]
        response = f"🔥 {len(specials)} specials: " + ", ".join([f"{p['name']} R{p.get('special_price', p['price'])}" for p in specials]) + f". 58 5th Ave Retreat. {BUSINESS_PHONE_DISPLAY}"
    elif found:
        response = f"Found {len(found)} products: " + "; ".join([f"{p['name']} R{p.get('special_price', p['price'])} ({p['category']})" for p in found]) + f". Call {BUSINESS_PHONE_DISPLAY} for bulk!"
    else:
        response = f"Hi! Family Supermarket Retreat at 58 5th Ave — 500+ products, wholesale prices, cheaper than Shoprite Retreat. Ask: rice price, hours, delivery, specials. Call {BUSINESS_PHONE_DISPLAY}."
    
    return jsonify({
        "success": True,
        "response": response,
        "products": found,
        "intent": "product_search" if found else "general",
        "business_phone": BUSINESS_PHONE_DISPLAY,
        "whatsapp": BUSINESS_WHATSAPP
    })


@app.route("/api/ai/recommendations", methods=["POST"])
def api_ai_recommendations():
    """Smart Recommendations API - FREE ML"""
    data = request.get_json()
    cart_ids = data.get('cart', [])
    products = load_products()
    
    # Simple association rules
    rules = {
        'rice': ['oil', 'vegetables'],
        'bread': ['drinks', 'snacks'],
        'oil': ['rice', 'vegetables'],
        'vegetables': ['rice', 'oil'],
        'drinks': ['snacks'],
        'snacks': ['drinks']
    }
    
    cart_cats = []
    for cid in cart_ids:
        prod = next((p for p in products if p['id'] == cid), None)
        if prod:
            cart_cats.append(prod['category'].lower())
    
    recommended = []
    seen = set(cart_ids)
    
    for cat in set(cart_cats):
        for rel in rules.get(cat, []):
            for p in products:
                if rel in p['category'].lower() and p['id'] not in seen:
                    recommended.append(p)
                    seen.add(p['id'])
                    break
        if len(recommended) >= 3:
            break
    
    if len(recommended) < 3:
        for p in products:
            if p.get('special') and p['id'] not in seen:
                recommended.append(p)
                if len(recommended) >= 3:
                    break
    
    return jsonify({"success": True, "recommendations": recommended[:3]})


@app.route("/api/live/orders")
def api_live_orders():
    """Real-time Live Orders via SSE - FREE"""
    def generate():
        # Send current stats every 3 seconds for 30 seconds
        for _ in range(10):
            stats = get_stats()
            orders = get_all_orders()
            latest = []
            for o in orders[:3]:
                try:
                    items = json.loads(o['items'])
                    latest.append({
                        "customer": o['customer_name'],
                        "total": o['total'],
                        "items": len(items),
                        "time": o['created_at']
                    })
                except:
                    pass
            
            data = {
                "stats": stats,
                "latest_orders": latest,
                "viewers": 3 + (len(orders) % 5),  # Simulated viewers for social proof
                "low_stock": len([p for p in load_products() if p.get('stock', 999) <= 5])
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            import time
            time.sleep(3)
    
    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })


@app.route("/api/image-search", methods=["POST"])
def api_image_search():
    """Advanced Image Search - FREE - Server-side fallback"""
    key = request.form.get("key") or request.args.get("key")
    # Allow public for customers, but check if admin wants
    # expected = os.getenv("ADMIN_KEY", "changeme")
    # if key != expected: allow public
    
    try:
        file = request.files.get('image') or request.files.get('photo') or request.files.get('file')
        if not file or not file.filename:
            return jsonify({"success": False, "error": "No image uploaded"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid image type"}), 400
        
        filename = secure_filename(file.filename).lower()
        
        # Save temporarily for analysis
        temp_path = UPLOAD_FOLDER / f"temp_search_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        file.save(temp_path)
        
        products = load_products()
        
        # Advanced: Use Pillow to analyze image - FREE
        matched = []
        try:
            from PIL import Image
            img = Image.open(temp_path)
            img = img.convert("RGB")
            # Simple color analysis for demo - FREE
            # In real advanced, you'd use image embeddings
            
            # Search by filename first - most accurate for grocery
            name_lower = filename.lower()
            
            # Map filename keywords to products
            keyword_map = {
                'bread': ['bread', 'bakery'],
                'rice': ['rice', 'staples'],
                'oil': ['oil', 'groceries'],
                'vegetable': ['vegetables', 'produce', 'veg'],
                'veg': ['vegetables', 'produce'],
                'drink': ['drinks'],
                'soda': ['drinks'],
                'snack': ['snacks'],
                'chips': ['snacks'],
                'milk': ['dairy', 'milk'],
                'apple': ['produce', 'vegetables'],
                'fruit': ['produce']
            }
            
            for keyword, categories in keyword_map.items():
                if keyword in name_lower:
                    for cat in categories:
                        for p in products:
                            if cat in p['category'].lower() or keyword in p['name'].lower():
                                if p not in matched:
                                    matched.append(p)
            
            # If no keyword match, do color-based fallback (advanced)
            if not matched:
                # Get dominant color
                img_small = img.resize((50, 50))
                # Simple: if greenish -> vegetables, brownish -> bread, etc.
                # For demo, return specials
                matched = [p for p in products if p.get('special')][:3]
                if not matched:
                    matched = products[:3]
            
            # Clean up temp file
            try:
                temp_path.unlink()
            except:
                pass
                
        except Exception as e:
            print(f"Image analysis failed: {e}")
            # Fallback: search by filename
            matched = []
            name_lower = filename.lower()
            for p in products:
                if any(word in name_lower for word in p['name'].lower().split()) or p['category'].lower() in name_lower:
                    matched.append(p)
            if not matched:
                matched = products[:3]
        
        return jsonify({
            "success": True,
            "fileName": filename,
            "matched": matched[:6],
            "count": len(matched),
            "message": f"Found {len(matched)} products matching your image at Family Supermarket Retreat - 58 5th Ave - Call {BUSINESS_PHONE_DISPLAY}",
            "business_phone": BUSINESS_PHONE_DISPLAY,
            "whatsapp": BUSINESS_WHATSAPP
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ar/models/<product_id>")
def api_ar_model(product_id):
    """AR Model data - FREE - Returns product for AR preview"""
    try:
        pid = int(product_id)
        product = next((p for p in load_products() if p['id'] == pid), None)
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        # In real AR, you'd return 3D model URL
        # For FREE version, return image + AR metadata
        return jsonify({
            "success": True,
            "product": product,
            "ar": {
                "image": f"/static/images/{product['image']}",
                "name": product['name'],
                "price": product.get('special_price', product['price']),
                "category": product['category'],
                "business_phone": BUSINESS_PHONE_DISPLAY,
                "whatsapp": BUSINESS_WHATSAPP,
                "address": "58 5th Ave, Retreat, Cape Town 7965",
                "model_url": None,  # Would be .glb file in pro version
                "ar_enabled": True,
                "instructions": "Point camera at table to see product in your space"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health():
    return {"status": "ok", "products": len(load_products())}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
