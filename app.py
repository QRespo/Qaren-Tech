from flask import Flask, render_template, abort
import sqlite3

app = Flask(__name__)

# ترتيب ثابت للمتاجر عشان تطلع بنفس الترتيب دايمًا حتى لو ما فيها سعر لمنتج معين
FIXED_STORE_ORDER = ["أمازون", "علي إكسبريس", "جرير", "إكسترا", "تيمو"]

def get_db():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_stores(conn):
    rows = conn.execute('SELECT DISTINCT store FROM offers').fetchall()
    stores = set(r['store'] for r in rows)
    ordered = [s for s in FIXED_STORE_ORDER if s in stores]
    extra = sorted(s for s in stores if s not in FIXED_STORE_ORDER)
    return ordered + extra

def attach_offer_metadata(offers, all_stores):
    """يحسب أطوال الأشرطة، يحدد الرتبة، ويكمل المتاجر الناقصة كـ 'غير متاح'"""
    real_offers = [dict(o) for o in offers]
    lowest_price = real_offers[0]['price'] if real_offers else None

    if real_offers:
        max_price = max(o['price'] for o in real_offers)
        multiple_offers = len(real_offers) > 1
        for i, o in enumerate(real_offers):
            o['available'] = True
            o['is_cheapest'] = (i == 0) and multiple_offers
            o['rank'] = i + 1 if multiple_offers else None
            o['bar_width'] = max(35, round((o['price'] / max_price) * 100))

    present_stores = {o['store'] for o in real_offers}
    missing_stores = [s for s in all_stores if s not in present_stores]

    for s in missing_stores:
        real_offers.append({
            'store': s,
            'price': None,
            'product_url': None,
            'available': False,
            'is_cheapest': False,
            'rank': None,
            'bar_width': 0,
        })

    return real_offers, lowest_price

HOMEPAGE_MAX_OFFERS = 3  # عدد الأسعار اللي تطلع بالبطاقة الصغيرة، بغض النظر عن عدد المتاجر الكلي

def get_products_with_offers():
    conn = get_db()
    all_stores = get_all_stores(conn)
    products = conn.execute('SELECT * FROM products ORDER BY id').fetchall()

    result = []
    for product in products:
        raw_offers = conn.execute(
            'SELECT * FROM offers WHERE product_id = ? ORDER BY price ASC',
            (product['id'],)
        ).fetchall()
        offers, lowest_price = attach_offer_metadata(raw_offers, all_stores)
        real_offers = [o for o in offers if o['available']]

        # بالصفحة الرئيسية نعرض بس أرخص 3 أسعار حقيقية (بدون المتاجر الغير متاحة)
        # عشان البطاقة تبقى مرتبة حتى لو زاد عدد المتاجر مستقبلاً
        homepage_offers = real_offers[:HOMEPAGE_MAX_OFFERS]
        remaining_count = len(real_offers) - len(homepage_offers)

        result.append({
            'id': product['id'],
            'name': product['name'],
            'category': product['category'],
            'image_url': product['image_url'],
            'description': product['description'],
            'offers': homepage_offers,
            'remaining_stores_count': remaining_count,
            'lowest_price': lowest_price,
            'multiple_offers': len(real_offers) > 1,
        })

    conn.close()
    return result

@app.route('/')
def index():
    products = get_products_with_offers()
    categories = sorted(set(p['category'] for p in products))

    best_deal = None
    best_savings = 0
    for p in products:
        real_offers = [o for o in p['offers'] if o['available']]
        if len(real_offers) > 1:
            s = real_offers[-1]['price'] - real_offers[0]['price']
            if s > best_savings:
                best_savings = s
                best_deal = p

    return render_template(
        'index.html',
        products=products,
        categories=categories,
        best_deal=best_deal,
        best_savings=round(best_savings) if best_deal else None,
    )

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db()
    all_stores = get_all_stores(conn)
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        conn.close()
        abort(404)

    raw_offers = conn.execute(
        'SELECT * FROM offers WHERE product_id = ? ORDER BY price ASC',
        (product_id,)
    ).fetchall()
    offers, _ = attach_offer_metadata(raw_offers, all_stores)
    real_offers = [o for o in offers if o['available']]

    savings = None
    savings_percent = None
    if len(real_offers) > 1:
        savings = round(real_offers[-1]['price'] - real_offers[0]['price'])
        if real_offers[-1]['price'] > 0:
            savings_percent = round((savings / real_offers[-1]['price']) * 100)

    related = conn.execute(
        'SELECT * FROM products WHERE category = ? AND id != ? LIMIT 3',
        (product['category'], product_id)
    ).fetchall()

    related_with_prices = []
    for r in related:
        r_offers = conn.execute(
            'SELECT price FROM offers WHERE product_id = ? ORDER BY price ASC LIMIT 1',
            (r['id'],)
        ).fetchone()
        related_with_prices.append({
            'id': r['id'],
            'name': r['name'],
            'image_url': r['image_url'],
            'lowest_price': r_offers['price'] if r_offers else None,
        })

    conn.close()

    return render_template(
        'product.html',
        product=dict(product),
        offers=offers,
        savings=savings,
        savings_percent=savings_percent,
        related=related_with_prices,
    )

if __name__ == '__main__':
    app.run(debug=True)
