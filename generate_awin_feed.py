import os
import requests
import csv
import time

# --- CONFIGURATION ---
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")      # Your Shopify Admin API access token
SHOP_NAME = os.environ.get("SHOP_NAME")            # e.g., "yourshopname" (without .myshopify.com)
API_VERSION = '2025-01'
CSV_FILENAME = 'awin_feed.csv'
CURRENCY = 'GBP'
DOMAIN = os.environ.get("DOMAIN")                  # e.g. "amazon.com"

def get_next_page(link_header):
    if not link_header:
        return None
    parts = link_header.split(',')
    for part in parts:
        if 'rel="next"' in part:
            start = part.find('<') + 1
            end = part.find('>')
            return part[start:end]
    return None

def fetch_all_products():
    session = requests.Session()
    session.headers.update({
        "X-Shopify-Access-Token": ACCESS_TOKEN
    })
    url = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}/products.json?limit=250"
    products = []
    while url:
        print("Fetching:", url)
        response = session.get(url)
        if response.status_code != 200:
            print("Error:", response.text)
            time.sleep(5)  # Wait before retrying
            continue
        data = response.json()
        products.extend(data.get('products', []))
        url = get_next_page(response.headers.get('Link'))
        time.sleep(1)  # Respect rate limits
    return products

def generate_csv(products):
    with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        header = [
            "product_id", "product_name", "price", "currency", 
            "image_url", "deep_link", "in_stock", "last_updated", 
            "description", "brand", "product_type"
        ]
        writer.writerow(header)
        for product in products:
            title = product.get('title', '')
            description = product.get('body_html', '')
            vendor = product.get('vendor', '')
            product_type = product.get('product_type', '')
            updated_at = product.get('updated_at', '')
            handle = product.get('handle', '')
            
            image_obj = product.get('image')
            product_image = image_obj.get('src', '') if image_obj else ''
            if not product_image:
                print(f"Skipping product {title} due to missing image.")
                continue

            for variant in product.get('variants', []):
                variant_id = variant.get('id', '')
                price = variant.get('price', '')
                available = variant.get('available', False)
                variant_image_id = variant.get('image_id')
                variant_image_url = product_image
                if variant_image_id and product.get('images'):
                    for img in product.get('images'):
                        if img.get('id') == variant_image_id:
                            variant_image_url = img.get('src')
                            break
                deep_link = f"https://{DOMAIN}/products/{handle}?variant={variant_id}&utm_source=awin_affiliates&utm_medium=feeds&utm_campaign=custom_awin_feed"
                row = [
                    variant_id,
                    title,
                    price,
                    CURRENCY,
                    variant_image_url,
                    deep_link,
                    1 if available else 0,
                    updated_at,
                    description,
                    vendor,
                    product_type
                ]
                writer.writerow(row)
    print(f"CSV feed generated: {CSV_FILENAME}")

def main():
    print("Starting feed generation...")
    products = fetch_all_products()
    print(f"Fetched {len(products)} products.")
    generate_csv(products)
    print("Feed generation complete.")

if __name__ == '__main__':
    main()
