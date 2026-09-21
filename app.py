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
        {"id": 5, "name": "Mixed Snacks", "category": "Snacks", "price": 35, "unit": "pack", "image": "snacks.jpg",
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


# ✅ FIXED: inquiries route was missing!
@app.route("/inquiries")
def inquiries():
    key = request.args.get("key")
    expected = os.getenv("ADMIN_KEY", "changeme")
    # Allow viewing without key in debug, require key in production
    if os.getenv("FLASK_ENV") == "production" and key != expected:
        return "🔒 Not authorized. Add ?key=YOUR_KEY to the URL.", 403
    if key and key != expected and os.getenv("FLASK_ENV") != "production":
        # still check if key provided but wrong
        if key != expected:
            return "🔒 Wrong key. Check ADMIN_KEY.", 403

    all_inq = get_all_inquiries()
    return render_template("inquiries.html", inquiries=all_inq)


@app.route("/api/products")
def api_products():
    return jsonify(get_products(category=request.args.get('category'), search_query=request.args.get('q'),
                                specials_only=request.args.get('specials') == 'true'))


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
