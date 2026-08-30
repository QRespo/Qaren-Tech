import sqlite3

conn = sqlite3.connect('products.db')

conn.execute('DROP TABLE IF EXISTS offers')
conn.execute('DROP TABLE IF EXISTS products')

conn.execute('''
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    image_url TEXT
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

products = [
    ('PlayStation 5 Slim', 'أجهزة',
     'https://gmedia.playstation.com/is/image/SIEPDC/ps5-slim-console-front-1-en-14sep23'),
    ('شاشة قيمنق Asus 27 بوصة 144Hz', 'شاشات',
     'https://m.media-amazon.com/images/I/61LkYBvvChL._AC_SL1500_.jpg'),
    ('يد تحكم DualSense', 'ملحقات',
     'https://gmedia.playstation.com/is/image/SIEPDC/dualsense-wireless-controller-white-1-en-19sep23'),
    ('سماعة قيمنق Logitech G435', 'ملحقات',
     'https://m.media-amazon.com/images/I/61vzsO5A1SL._AC_SL1500_.jpg'),
]

product_ids = []
for p in products:
    cur = conn.execute(
        'INSERT INTO products (name, category, image_url) VALUES (?, ?, ?)', p
    )
    product_ids.append(cur.lastrowid)

offers = [
    (product_ids[0], 'جرير', 1899, '#'),
    (product_ids[0], 'إكسترا', 1949, '#'),
    (product_ids[0], 'أمازون', 1999, '#'),

    (product_ids[1], 'إكسترا', 899, '#'),
    (product_ids[1], 'أمازون', 949, '#'),
    (product_ids[1], 'نون', 979, '#'),

    (product_ids[2], 'جرير', 249, '#'),
    (product_ids[2], 'أمازون', 259, '#'),

    (product_ids[3], 'نون', 199, '#'),
    (product_ids[3], 'أمازون', 219, '#'),
    (product_ids[3], 'إكسترا', 229, '#'),
]

conn.executemany(
    'INSERT INTO offers (product_id, store, price, product_url) VALUES (?, ?, ?, ?)',
    offers
)

conn.commit()
conn.close()
print("تم إنشاء قاعدة البيانات وإضافة المنتجات والعروض بنجاح")
