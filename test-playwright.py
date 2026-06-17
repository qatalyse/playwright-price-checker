from playwright.sync_api import sync_playwright

urls = [
    "https://www.fairprice.com.sg/product/fairprice-white-bread-enriched-500g-13200672",
    "https://www.fairprice.com.sg/product/holland-potato-china-1kg-13057650",
]

def scrape():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            title = page.title()

            results.append({
                "url": url,
                "title": title
            })

        browser.close()

    return results


data = scrape()
for item in data:
    print(item)