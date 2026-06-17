from playwright.sync_api import sync_playwright

urls = [
    "https://www.fairprice.com.sg/product/fairprice-white-bread-enriched-500g-13200672",
    "https://www.fairprice.com.sg/product/holland-potato-china-1kg-13057650",
    "https://www.fairprice.com.sg/product/buttercup-luxury-spread-250g-366329",
    "https://www.fairprice.com.sg/product/pasar-fresh-eggs-10-eggs-550g-451724",
    "https://www.fairprice.com.sg/product/campbells-soup-mushroom-potage-305g-465098",
    "https://www.fairprice.com.sg/product/myojo-instant-noodles-ramen-char-mee-5s-x-75g-88577",
    "https://www.fairprice.com.sg/product/myojo-instant-noodles-mee-goreng-original-5s-x-80g-10647588",
    "https://www.fairprice.com.sg/product/indomie-mi-goreng-instant-noodles-special-5-x-85g-13057731"
]

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            # # TRY 1: meta price (often most stable)
            # meta_price = page.locator("meta[property='product:price:amount']").first
            # price = meta_price.get_attribute("content") if meta_price.count() > 0 else None

            # TRY 2: fallback visible price
            fallback = page.locator("text=/\\$\\s*[0-9]+\\.[0-9]{2}/").first
            fallback_price = fallback.inner_text() if fallback.count() > 0 else None

            print({
                "url": url,
                # "meta_price": price,
                "fallback_price": fallback_price
            })

        browser.close()

scrape()