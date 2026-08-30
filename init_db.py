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

# منتجات حقيقية بأسعار وروابط أفلييت حقيقية من أمازون السعودية
products = [
    ('بلايستيشن 5 سليم PlayStation 5 Slim', 'أجهزة',
     'https://commons.wikimedia.org/wiki/Special:FilePath/PS5DigitalEdition.png'),
    ('شاشة قيمنق أسوس VG27AQ5A-J (2560x1440)', 'شاشات',
     'https://commons.wikimedia.org/wiki/Special:FilePath/Computer_monitor.jpg'),
    ('شاشة قيمنق أسوس VG279QE5A (1920x1080)', 'شاشات',
     'https://commons.wikimedia.org/wiki/Special:FilePath/Computer_monitor.jpg'),
    ('سماعة قيمنق HyperX Cloud III أسود/أحمر', 'ملحقات',
     'https://commons.wikimedia.org/wiki/Special:FilePath/Xbox_One_Chat_Headset.jpg'),
    ('سماعة قيمنق HyperX Cloud 2', 'ملحقات',
     'https://commons.wikimedia.org/wiki/Special:FilePath/Xbox_One_Chat_Headset.jpg'),
]

product_ids = []
for p in products:
    cur = conn.execute(
        'INSERT INTO products (name, category, image_url) VALUES (?, ?, ?)', p
    )
    product_ids.append(cur.lastrowid)

# كل عرض هنا حقيقي: سعر حالي من صفحة المنتج + رابط أفلييت فيه رمزك (qarentech-21)
offers = [
    (product_ids[0], 'أمازون', 2394.00,
     'https://www.amazon.sa/dp/B0CN5Q73LC?linkCode=ll2&tag=qarentech-21&linkId=bf0cc645975a9d66f4d1ea8b26061361'),

    (product_ids[1], 'أمازون', 749.00,
     'https://www.amazon.sa/dp/B0GF8176TN?linkCode=ll2&tag=qarentech-21&linkId=9bfa37e7def11b0b6379d50bc1256162'),

    (product_ids[2], 'أمازون', 539.00,
     'https://www.amazon.sa/dp/B0F8NQZ4B4?linkCode=ll2&tag=qarentech-21&linkId=6f519e5186c349fa392335a216abb464'),

    (product_ids[3], 'أمازون', 255.00,
     'https://www.amazon.sa/dp/B0C3BV19Q3?linkCode=ll2&tag=qarentech-21&linkId=f31a929f613d5bf62357eea116d35bac'),

    (product_ids[4], 'أمازون', 186.50,
     'https://www.amazon.sa/dp/B00SAYCXWG?linkCode=ll2&tag=qarentech-21&linkId=ec0e685abc7f630fdfa28b33d80d6109'),
]

conn.executemany(
    'INSERT INTO offers (product_id, store, price, product_url) VALUES (?, ?, ?, ?)',
    offers
)

conn.commit()
conn.close()
print("تم إنشاء قاعدة البيانات وإضافة المنتجات الحقيقية بنجاح")
