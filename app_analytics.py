import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import json

DB_PATH = "inquiries.db"


def get_analytics():
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

    # Inquiries per day (last 14 days)
    cur.execute("""
        SELECT date(created_at) as day, COUNT(*) as count
        FROM inquiries
        WHERE created_at >= date('now', '-14 days')
        GROUP BY date(created_at)
        ORDER BY day
    """)
    inquiries_by_day_raw = cur.fetchall()

    # Generate last 14 days labels
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

    # Top products from orders (parse items json)
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
    try:
        products = json.loads(open('products.json').read().strip() or '[]')
    except:
        products = []

    category_count = defaultdict(int)
    for p in products:
        category_count[p.get('category', 'Other')] += 1

    conn.close()

    return {
        "days": [d[5:] for d in days],  # MM-DD format
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


if __name__ == "__main__":
    print(get_analytics())
