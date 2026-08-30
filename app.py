from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_products():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    products = conn.execute('SELECT * FROM products ORDER BY id').fetchall()
    conn.close()
    return products

@app.route('/')
def index():
    products = get_products()
    return render_template('index.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)
