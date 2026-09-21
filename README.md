# 🛒 Family Supermarket & Wholesalers — Retreat, Cape Town

**Live:** Your Render URL | **Stack:** Python Flask (100% FREE)

Modern, motion-rich e-commerce supermarket with cart + admin dashboard + sales analytics. Built for Retreat, Cape Town — no paid services, no API keys needed.

## ✨ Features (All FREE)

- 🎨 **Premium UI** — Glassmorphism navbar, 3D tilt cards, stagger reveal
- 🔍 **Search & Filters** — Python-powered search `/?q=rice`
- 🛒 **Cart + WhatsApp Checkout** — Fly-to-cart animation, saves orders to SQLite, opens WhatsApp (FREE)
- 📊 **Admin Dashboard** — `/admin?key=changeme` — Edit products live, view orders, revenue charts
- 📈 **Analytics** — Revenue last 14 days, category breakdown, top products
- 🚀 **SEO Ready** — `/sitemap.xml`, `/robots.txt`

## 🆓 100% Free Stack

| Service | Cost |
|---------|------|
| Hosting | FREE - Render Free Tier |
| Database | FREE - SQLite |
| Charts | FREE - Chart.js CDN |
| Checkout | FREE - WhatsApp link |

## 🚀 Quick Start

```bash
git clone https://github.com/samahmed18156/family-supermarket.git
cd family-supermarket
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:5000
# Admin: http://127.0.0.1:5000/admin?key=changeme
```

## 📦 Edit Products

Edit `products.json`:

```json
{
  "id": 7,
  "name": "Milk 2L",
  "category": "Dairy",
  "price": 32.00,
  "unit": "bottle",
  "image": "milk.jpg",
  "in_stock": true,
  "special": true,
  "special_price": 27.00
}
```

## 🛠️ Free Tools in utils/

### Bulk Excel Import (FREE)
```bash
pip install openpyxl
python utils/bulk_import.py
# Creates products_template.xlsx - edit it
python utils/bulk_import.py products_template.xlsx
```

### Image Optimizer (FREE)
```bash
python utils/image_optimizer.py
# Converts JPG → WebP, 70% smaller
```

## 📍 Store Info

58 5th Ave, Retreat, Cape Town, 7965
📞 079 623 2189

Built with Python + Free tools. R0/month.