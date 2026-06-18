from playwright.sync_api import sync_playwright
import pandas as pd
import re

urls = [
    "https://www.fairprice.com.sg/product/fairprice-white-bread-enriched-500g-13200672",
    "https://www.fairprice.com.sg/product/holland-potato-china-1kg-13057650",
    "https://www.fairprice.com.sg/product/fairprice-butter-salted-250g-13218509",
    # "https://www.fairprice.com.sg/product/fairprice-uht-milk-full-cream-1lt-11898581",
    "https://www.fairprice.com.sg/product/farm-fresh-milk-lactose-free-1l-13287428",
    # "https://www.fairprice.com.sg/product/buttercup-luxury-spread-250g-366329",
    "https://www.fairprice.com.sg/product/pasar-fresh-eggs-10-eggs-550g-451724",
    "https://www.fairprice.com.sg/product/campbells-soup-mushroom-potage-305g-465098",
    "https://www.fairprice.com.sg/product/myojo-instant-noodles-ramen-char-mee-5s-x-75g-88577",
    "https://www.fairprice.com.sg/product/myojo-instant-noodles-mee-goreng-original-5s-x-80g-10647588",
    "https://www.fairprice.com.sg/product/indomie-mi-goreng-instant-noodles-special-5-x-85g-13057731"
]
def pick_main_price(prices):
    # remove unit pricing like $0.41/100g (future improvement)
    # cleaned = [p for p in prices if "/100g" not in p and "/kg" not in p]
    
    # return cleaned[0] if cleaned else None
    return prices[0] if prices else None

def original_price(prices):
    return prices[1] if len(prices) == 2 else ''
        
def clean_title(title: str) -> str:
    if not title:
        return None
    return title.split("|")[0].strip()

import re

# def extract_quantity_weight(text):
#     text = text.lower()

#     # -------------------
#     # 1. extract weight
#     # -------------------
#     weight_match = re.search(r"([\d.]+\s*(?:g|kg))", text)
#     weight = weight_match.group(1).replace(" ", "") if weight_match else None

#     # -------------------
#     # 2. extract quantity (case A: "3 x")
#     # -------------------
#     qty_match = re.search(r"(\d+)\s*x", text)
#     quantity = int(qty_match.group(1)) if qty_match else None

#     # -------------------
#     # 3. extract quantity (case B: "(10 per pack)")
#     # -------------------
#     if quantity is None:
#         pack_match = re.search(r"\((\d+)\s*per\s*pack\)", text)
#         if pack_match:
#             quantity = int(pack_match.group(1))

#     # -------------------
#     # 4. fallback
#     # -------------------
#     if quantity is None:
#         quantity = 1

#     return quantity, weight

def extract_from_url(url,title):
    slug = url.lower()

    # -------------------------
    # 1. weight (always exists if present)
    # -------------------------
    weight_match = re.search(r"(\d+(?:\.\d+)?\s*(?:g|kg|l))", slug)
    weight = weight_match.group(1).replace(" ", "") if weight_match else None

    # -------------------------
    # 2. quantity patterns (multiple formats)
    # -------------------------

    quantity = None

    # case A: "10-eggs", "3-packs"
    match = re.search(r"-(\d+)-[a-z]", slug)
    if match:
        quantity = int(match.group(1))

    # case B: "5x75g" or "5-x-75g"
    if quantity is None:
        match = re.search(r"(\d+)\s*-?\s*x\s*-?\s*\d+\s*(?:g|kg)", slug)
        if match:
            quantity = int(match.group(1))

    # case C: "5s-x-75g"
    if quantity is None:
        match = re.search(r"(\d+)s?-x-\d+", slug)
        if match:
            quantity = int(match.group(1))

    # fallback
    if quantity is None:
        quantity = 1

    servings = 1
    if quantity == 1 and 'Potato' in title:
        servings = float(weight.replace("kg","")) / 0.2
    if quantity == 1 and 'Butter' in title:
        servings = int(weight.replace("g","")) / 10
    if quantity == 1 and 'Campbell' in title:
        servings = 3
    if quantity == 1 and 'Bread' in title:
        servings = 7
    if quantity == 1 and 'Milk' in title:
        servings = 10
    

    # -------------------------
    # 3. product id
    # -------------------------
    # product_id = slug.rstrip("/").split("-")[-1]

    # return quantity if end_type == 'qty' else weight
    return quantity, weight, servings
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

            
            promo_validity = ''
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

            # # 3. CALL URL FUNCTION HERE 👇
            # quantity, weight = extract_from_url(url)
            quantity, weight, servings = extract_from_url(url, title)

            # quantity, weight = extract_quantity_weight(title)

            # STORE ROW
            results.append({
                # "name": title,
                "product_name": clean_title(title),
                "quantity": quantity,
                "weight": weight,
                "current_price": main_price,
                # "all_prices": prices,
                "original_price": original_price(prices),
                "promo_validity": promo_validity,
                "servings": round(servings if servings > 1 else quantity),
                "cost_per_unit": f"${round((float(main_price.replace("$", "")) / quantity / servings), 2)}"
                # "url": url
            })           

        browser.close()
        
        df = pd.DataFrame(results)

        df["current_price_num"] = df["current_price"].str.replace("$", "").astype(float)
        df["cost_per_unit_num"] = df["cost_per_unit"].str.replace("$", "").astype(float)

        total_cost = df["current_price_num"].sum()
        total_cost_per_unit = df["cost_per_unit_num"].sum()

        # print({
        #     "url": url,
        #     "prices_found": prices,
        #     "main_price": main_price,
        #     "promo_validity": promo_validity
        # })
        total_row = {
            "product_name": "TOTAL",
            "quantity": "",
            "weight": "",
            "current_price": f"${round(total_cost, 2)}",
            "original_price": "",
            "promo_validity": "",
            "servings":"",
            "cost_per_unit": f"${round(total_cost_per_unit, 2)}"
        }

        # df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        results.append(total_row)

    return results

# RUN + EXPORT
data = scrape()

df = pd.DataFrame(data)
# Save Excel file
# df.to_excel("fairprice_prices.xlsx", index=False)

# print(df)
# print("\nSaved to fairprice_prices.xlsx")

html = df.to_html(index=False, classes="table table-striped table-bordered", border=0)

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

        /* 🔥 key fix: left align everything cleanly */
        table th, table td {{
            text-align: left !important;
            vertical-align: middle;
        }}

        /* optional: make headers slightly stronger */
        table th {{
            font-weight: 600;
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