from playwright.sync_api import sync_playwright
import pandas as pd

urls = [
    # "https://www.fairprice.com.sg/product/fairprice-white-bread-enriched-500g-13200672",
    # "https://www.fairprice.com.sg/product/holland-potato-china-1kg-13057650",
    # "https://www.fairprice.com.sg/product/buttercup-luxury-spread-250g-366329",
    # "https://www.fairprice.com.sg/product/pasar-fresh-eggs-10-eggs-550g-451724",
    # "https://www.fairprice.com.sg/product/campbells-soup-mushroom-potage-305g-465098",
    "https://www.fairprice.com.sg/product/myojo-instant-noodles-ramen-char-mee-5s-x-75g-88577",
    "https://www.fairprice.com.sg/product/myojo-instant-noodles-mee-goreng-original-5s-x-80g-10647588",
    # "https://www.fairprice.com.sg/product/indomie-mi-goreng-instant-noodles-special-5-x-85g-13057731"
]
def pick_main_price(prices):
    # remove unit pricing like $0.41/100g (future improvement)
    # cleaned = [p for p in prices if "/100g" not in p and "/kg" not in p]
    
    # return cleaned[0] if cleaned else None
    return prices[0] if prices else None

def scrape():
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            # 1. Wait for page to fully render something price-related
            page.wait_for_selector("text=$", timeout=10000)

            # # 2. Grab ALL visible dollar prices
            # price_elements = page.locator("text=/\\$\\s*\\d+\\.\\d{2}/")
            # STRICT price-only match
            price_elements = page.locator("text=/^\\$\\s*\\d+\\.\\d{2}$/")
            
            promo_locator = page.locator("text=/Till\\s+/i")
            promo_validity = None
            if promo_locator.count() > 0:
              promo_validity = promo_locator.first.inner_text().strip()
    
            prices = []
            for i in range(price_elements.count()):
                prices.append(price_elements.nth(i).inner_text().strip())

            # 3. Heuristic: main price is usually the FIRST large visible one
            # main_price = prices[0] if prices else None
            main_price = pick_main_price(prices)

            # PRODUCT NAME (simple but reliable fallback)
            title = page.title()

            # STORE ROW
            results.append({
                "name": title,
                "main_price": main_price,
                "all_prices": prices,
                "promo_validity": promo_validity,
                # "url": url
            })

            # print({
            #     "url": url,
            #     "prices_found": prices,
            #     "main_price": main_price,
            #     "promo_validity": promo_validity
            # })
            

        browser.close()
    
    return results

# RUN + EXPORT
data = scrape()

df = pd.DataFrame(data)

# Save Excel file
# df.to_excel("fairprice_prices.xlsx", index=False)

# print(df)
# print("\nSaved to fairprice_prices.xlsx")

html = df.to_html(index=False, classes="table table-striped")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>FairPrice Tracker</title>

    <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

    <style>
        body {{
            background: #f8f9fa;
        }}
        h2 {{
            margin-bottom: 20px;
        }}
        .table {{
            background: white;
        }}
    </style>
</head>

<body class="p-4">
    <h2>🛒 FairPrice Tracker</h2>
    <p>Last updated automatically via GitHub Actions</p>

    {html}

</body>
</html>
    """)