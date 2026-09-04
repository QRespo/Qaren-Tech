import sqlite3
import openpyxl

wb = openpyxl.load_workbook('products.xlsx', data_only=True)
ws = wb['المنتجات']

conn = sqlite3.connect('products.db')

conn.execute('DROP TABLE IF EXISTS offers')
conn.execute('DROP TABLE IF EXISTS products')

conn.execute('''
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    image_url TEXT,
    description TEXT
)
''')

conn.execute('''
CREATE TABLE offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    store TEXT NOT NULL,
    price REAL NOT NULL,
    product_url TEXT,
    FOREIGN KEY (product_id) REFERENCES products (id)
)
''')

product_id_by_name = {}
count_products = 0
count_offers = 0

for row in ws.iter_rows(min_row=2, values_only=True):
    if not row or not row[0]:
        continue
    name, category, image_url, store, price, product_url = row[:6]
    description = row[6] if len(row) > 6 else None
    if name is None or store is None or price is None:
        continue

    if name not in product_id_by_name:
        cur = conn.execute(
            'INSERT INTO products (name, category, image_url, description) VALUES (?, ?, ?, ?)',
            (name, category, image_url, description)
        )
        product_id_by_name[name] = cur.lastrowid
        count_products += 1

    conn.execute(
        'INSERT INTO offers (product_id, store, price, product_url) VALUES (?, ?, ?, ?)',
        (product_id_by_name[name], store, float(price), product_url)
    )
    count_offers += 1

conn.commit()
conn.close()
print(f"تم بناء قاعدة البيانات من ملف Excel: {count_products} منتج، {count_offers} عرض سعر")
