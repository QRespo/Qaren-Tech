"""
سكربت تحديث الأسعار تلقائيًا.
يقرأ products.xlsx، ولكل صف من علي إكسبريس أو نون، يجيب السعر الحالي
ويحدّثه بالملف مباشرة. بعد التشغيل، شغّل python init_db.py عشان
الموقع يستخدم الأسعار الجديدة.

الإعداد المطلوب قبل أول تشغيل:
1. انسخ ملف .env.example وسمّه .env
2. عبّي بيانات علي إكسبريس (App Key, App Secret, Tracking ID) بملف .env
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
import openpyxl
from dotenv import load_dotenv

load_dotenv()

ALIEXPRESS_APP_KEY = os.getenv("ALIEXPRESS_APP_KEY")
ALIEXPRESS_APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
ALIEXPRESS_TRACKING_ID = os.getenv("ALIEXPRESS_TRACKING_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

REQUEST_TIMEOUT_SECONDS = 30

REQUEST_DELAY_SECONDS = 5  # تأخير محترم بين كل طلب وطلب
RATE_LIMIT_RETRY_SECONDS = 3  # وقت إضافي لو صادفنا حد أقصى للطلبات


# ============ علي إكسبريس (عبر الـ API الرسمي) ============

# الريال السعودي مربوط بسعر ثابت بالدولار الأمريكي (سعر صرف رسمي، مو تقريبي)
USD_TO_SAR = 3.75

def get_aliexpress_client():
    from aliexpress_api import AliexpressApi, models
    if not (ALIEXPRESS_APP_KEY and ALIEXPRESS_APP_SECRET and ALIEXPRESS_TRACKING_ID):
        raise RuntimeError(
            "بيانات علي إكسبريس ناقصة. تأكد من ملف .env فيه القيم الثلاث."
        )
    # المكتبة ما تدعم الريال السعودي مباشرة، فنستخدم الدولار ونحوّله بالكود
    return AliexpressApi(
        ALIEXPRESS_APP_KEY,
        ALIEXPRESS_APP_SECRET,
        models.Language.AR,
        models.Currency.USD,
        ALIEXPRESS_TRACKING_ID,
    )


def resolve_final_url(short_url):
    """يفك رابط الأفلييت المختصر ويرجع الرابط الأصلي الكامل"""
    resp = requests.get(short_url, headers=HEADERS, allow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS)
    return resp.url


def extract_aliexpress_product_id(url):
    match = re.search(r'/item/(\d+)\.html', url)
    return match.group(1) if match else None


def fetch_aliexpress_price(short_url, client, retry=True):
    final_url = resolve_final_url(short_url)
    product_id = extract_aliexpress_product_id(final_url)
    if not product_id:
        print(f"  ⚠️  ما قدرت أستخرج رقم المنتج من: {final_url}")
        return None

    try:
        products = client.get_products_details([product_id])
    except Exception as e:
        if "frequency exceeds" in str(e).lower() and retry:
            print(f"  ... تجاوزنا الحد المسموح للحظة، ننتظر {RATE_LIMIT_RETRY_SECONDS} ثواني ونعيد المحاولة")
            time.sleep(RATE_LIMIT_RETRY_SECONDS)
            return fetch_aliexpress_price(short_url, client, retry=False)
        raise

    if not products:
        print(f"  ⚠️  ما رجع المنتج أي بيانات: {product_id}")
        return None

    price_usd = products[0].target_sale_price or products[0].target_original_price
    if not price_usd:
        return None
    price_sar = float(price_usd) * USD_TO_SAR
    return round(price_sar, 2)


# ============ نون (قراءة خفيفة من صفحة المنتج) ============

def fetch_noon_price(short_url):
    # نستخدم curl_cffi بدل requests العادية، عشان يقلّد "بصمة" متصفح كروم حقيقي
    # (requests العادية تنكشف وتنحظر من أنظمة الحماية المتقدمة زي اللي عند نون)
    from curl_cffi import requests as curl_requests

    print(f"  ... جاري الاتصال بـ {short_url} (بتقليد متصفح كروم)")
    resp = curl_requests.get(
        short_url,
        headers=HEADERS,
        allow_redirects=True,
        timeout=REQUEST_TIMEOUT_SECONDS,
        impersonate="chrome124",
    )
    print(f"  ... وصل رد، الرابط النهائي: {resp.url}")
    soup = BeautifulSoup(resp.text, "html.parser")

    # محاولة 1: وسم meta شائع بمواقع التجارة الإلكترونية
    meta_price = soup.find("meta", {"property": "product:price:amount"})
    if meta_price and meta_price.get("content"):
        return float(meta_price["content"])

    # محاولة 2: أي عنصر فيه itemprop="price"
    itemprop_price = soup.find(attrs={"itemprop": "price"})
    if itemprop_price:
        content = itemprop_price.get("content") or itemprop_price.text
        digits = re.sub(r'[^\d.]', '', content)
        if digits:
            return float(digits)

    # محاولة 3: بيانات مضمّنة بصيغة JSON داخل script (شائع بمواقع React/Next.js)
    import json

    def search_price_in_json(obj, keys_priority=("sellingprice", "saleprice", "currentprice", "price")):
        """يدور داخل أي JSON متداخل عن أقرب مفتاح اسمه يشبه 'price'"""
        found = {}
        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    kl = k.lower()
                    if isinstance(v, (int, float)) and any(p in kl for p in keys_priority):
                        found.setdefault(kl, v)
                    walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(obj)
        for key in keys_priority:
            for found_key, value in found.items():
                if key in found_key:
                    return value
        return None

    for script in soup.find_all("script"):
        script_text = script.string
        if not script_text or 'price' not in script_text.lower():
            continue

        candidates = [script_text]
        # أنماط شائعة زي: window.__INITIAL_STATE__ = {...};
        assignment_match = re.search(r'=\s*(\{.*\})\s*;?\s*$', script_text.strip(), re.DOTALL)
        if assignment_match:
            candidates.append(assignment_match.group(1))

        for candidate in candidates:
            try:
                data = json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                continue
            price = search_price_in_json(data)
            if price:
                return float(price)

    # لو ما لقينا شي، نحفظ نسخة من الصفحة عشان نفحصها يدويًا سوا
    debug_filename = "noon_debug_last_failed.html"
    with open(debug_filename, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"  ⚠️  ما قدرت ألقى السعر تلقائيًا. حفظت نسخة من الصفحة بملف: {debug_filename}")
    print("      افتحه بمتصفحك، اضغط Ctrl+F ودور على السعر اللي تعرفه (مثلاً 2439)،")
    print("      وأرسل لي جزء من الكود المحيط فيه عشان أظبط الاستخراج بدقة.")
    return None


# ============ التشغيل الرئيسي ============

def main():
    wb = openpyxl.load_workbook('products.xlsx')
    ws = wb['المنتجات']

    aliexpress_client = None
    try:
        aliexpress_client = get_aliexpress_client()
    except RuntimeError as e:
        print(f"تنبيه: {e}")
        print("راح نتخطى تحديث علي إكسبريس هالمرة.\n")

    updated_count = 0
    failed_count = 0

    for row in ws.iter_rows(min_row=2):
        name_cell, category_cell, image_cell, store_cell, price_cell, url_cell = row[:6]
        if not name_cell.value or not store_cell.value or not url_cell.value:
            continue

        store = store_cell.value
        url = url_cell.value
        old_price = price_cell.value

        new_price = None

        if store == "علي إكسبريس" and aliexpress_client:
            print(f"جاري تحديث (علي إكسبريس): {name_cell.value}")
            try:
                new_price = fetch_aliexpress_price(url, aliexpress_client)
            except Exception as e:
                print(f"  ❌ خطأ: {e}")

        elif store == "نون":
            print(f"جاري تحديث (نون): {name_cell.value}")
            try:
                new_price = fetch_noon_price(url)
            except Exception as e:
                print(f"  ❌ خطأ: {e}")

        else:
            continue

        if new_price:
            price_cell.value = new_price
            print(f"  ✅ السعر القديم: {old_price} → الجديد: {new_price}")
            updated_count += 1
        else:
            failed_count += 1

        time.sleep(REQUEST_DELAY_SECONDS)

    wb.save('products.xlsx')
    print(f"\nخلص التحديث. نجح: {updated_count}, فشل: {failed_count}")
    print("شغّل الآن: python init_db.py")


if __name__ == '__main__':
    main()
