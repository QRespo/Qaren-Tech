from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_products_with_offers():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row

    products = conn.execute('SELECT * FROM products ORDER BY id').fetchall()

    result = []
    for product in products:
        offers = conn.execute(
            'SELECT * FROM offers WHERE product_id = ? ORDER BY price ASC',
            (product['id'],)
        ).fetchall()

        offers = [dict(o) for o in offers]
        if offers:
            max_price = max(o['price'] for o in offers)
            multiple_offers = len(offers) > 1
            for i, o in enumerate(offers):
                o['is_cheapest'] = (i == 0) and multiple_offers
                # نسبة طول الشريط مقارنة بأغلى سعر، بحد أدنى 35% عشان الشريط يبان دايمًا
                o['bar_width'] = max(35, round((o['price'] / max_price) * 100))

        result.append({
            'id': product['id'],
            'name': product['name'],
            'category': product['category'],
            'image_url': product['image_url'],
            'offers': offers,
            'lowest_price': offers[0]['price'] if offers else None,
            'multiple_offers': len(offers) > 1,
        })

    conn.close()
    return result

@app.route('/')
def index():
    products = get_products_with_offers()
    categories = sorted(set(p['category'] for p in products))
    return render_template('index.html', products=products, categories=categories)

if __name__ == '__main__':
    app.run(debug=True)
