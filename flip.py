# ======================================
# Flipkart Professional Multi-Threaded Scraper
# ======================================

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------------------------------------
# CONFIG
# --------------------------------------
BASE_URL = "https://www.flipkart.com/womens-footwear/pr?sid=osp,iko&page={}"
MAX_PAGES = 10  # number of pages to scrape
SCROLL_DELAY = (1, 2)
REQUEST_DELAY = (0.2, 0.5)
OUTPUT_FILE = "flipkart_products_fast_multithread.csv"
MAX_THREADS = 10  # number of parallel threads

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

# --------------------------------------
# SELENIUM DRIVER
# --------------------------------------
def create_driver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--blink-settings=imagesEnabled=false")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver, WebDriverWait(driver, 20)

# --------------------------------------
# PHASE 1: COLLECT PRODUCT LINKS
# --------------------------------------
def collect_links():
    driver, wait = create_driver()
    product_links = set()

    for page in range(1, MAX_PAGES + 1):
        print(f"[PAGE] {page}")
        driver.get(BASE_URL.format(page))
        time.sleep(random.uniform(*SCROLL_DELAY))

        # Close login popup safely
        try:
            wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z"))
            ).click()
        except:
            pass

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(*SCROLL_DELAY))

        try:
            anchors = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "a[href*='/p/']")
                )
            )
        except:
            print("⚠️ Failed to load products")
            continue

        for a in anchors:
            link = a.get_attribute("href")
            if link:
                product_links.add(link)

        print(f"Collected so far: {len(product_links)} links")

    driver.quit()
    return list(product_links)

# --------------------------------------
# PHASE 2: SCRAPE PRODUCT DETAILS (FAST)
# --------------------------------------
def scrape_product(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        def meta(prop):
            tag = soup.find("meta", {"property": prop})
            return tag["content"] if tag else ""

        title = meta("og:title")
        image = meta("og:image")

        price = ""
        price_tag = soup.find(string=lambda x: x and "₹" in x)
        if price_tag:
            price = price_tag.strip()

        return {
            "title": title,
            "price": price,
            "image": image,
            "link": url
        }

    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None

# --------------------------------------
# MAIN
# --------------------------------------
def main():
    print("\n🚀 Collecting product links...")
    links = collect_links()
    print(f"\n✅ Total unique product links: {len(links)}")

    print("\n⚡ Scraping product details (MULTI-THREAD)...")
    products = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_url = {executor.submit(scrape_product, link): link for link in links}

        for i, future in enumerate(as_completed(future_to_url), 1):
            data = future.result()
            if data:
                products.append(data)

            # Optional small delay to avoid blocking
            time.sleep(random.uniform(*REQUEST_DELAY))

            # Print progress
            if i % 20 == 0 or i == len(links):
                print(f"[PRODUCTS SCRAPED] {i}/{len(links)}")
                # Save periodically
                df = pd.DataFrame(products)
                df.to_csv(OUTPUT_FILE, index=False)

    # Final save
    df = pd.DataFrame(products)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n🎉 DONE! Scraped {len(products)} products to {OUTPUT_FILE}")

# --------------------------------------
# RUN
# --------------------------------------
if __name__ == "__main__":
    main()
