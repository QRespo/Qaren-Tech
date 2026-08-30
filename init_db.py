import sqlite3

conn = sqlite3.connect('products.db')

conn.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL,
    store TEXT NOT NULL,
    image_url TEXT
)
''')

# نمسح البيانات القديمة عشان ما تتكرر لو شغلت الملف أكثر من مرة
conn.execute('DELETE FROM products')

products = [
    ('PlayStation 5 Slim', 'أجهزة', 1899, 'جرير',
     'https://gmedia.playstation.com/is/image/SIEPDC/ps5-slim-console-front-1-en-14sep23'),
    ('Asus Monitor 1080p 144Hz', 'شاشات', 899, 'إكسترا',
     'https://m.media-amazon.com/images/I/61LkYBvvChL._AC_SL1500_.jpg'),
]

conn.executemany(
    'INSERT INTO products (name, category, price, store, image_url) VALUES (?, ?, ?, ?, ?)',
    products
)

conn.commit()
conn.close()
print("تم إنشاء قاعدة البيانات وإضافة المنتجات بنجاح")
