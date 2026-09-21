import os, json, sqlite3
from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo
from functools import lru_cache
from flask import Flask, render_template, request, jsonify, Response

from dotenv import load_dotenv

load_dotenv()

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
        "specials_count": len([p for p in load_products() if p.get('special')])
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
        "whatsapp_url": f"https://wa.me/27796232189?text={wa_text}"
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

    # Validate
    try:
        # Save to file
        Path("products.json").write_text(json.dumps(new_products, indent=2))
        # Clear cache
        load_products.cache_clear()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/admin/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/admin/analytics")
def api_analytics():
    return jsonify(get_analytics())


@app.route("/sitemap.xml")
def sitemap():
    base = request.host_url.rstrip('/')
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base}/</loc><priority>1.0</priority></url><url><loc>{base}/specials</loc><priority>0.9</priority></url><url><loc>{base}/about</loc><priority>0.8</priority></url></urlset>'
    return Response(xml, mimetype='application/xml')


@app.route("/robots.txt")
def robots():
    return Response(f"User-agent: *\nAllow: /\nSitemap: {request.host_url.rstrip('/')}/sitemap.xml\n",
                    mimetype='text/plain')


@app.route("/health")
def health():
    return {"status": "ok", "products": len(load_products())}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
