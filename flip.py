# ======================================
# Flipkart Professional Full Multi-Threaded Scraper
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
BASE_URL = "https://www.flipkart.com/womens-footwear/pr?sid=osp,iko&fm=neo%2Fmerchandising&page={}"
SCROLL_DELAY = (1, 2)
REQUEST_DELAY = (0.2, 0.5)
OUTPUT_FILE = "flip_products_all_pages.csv"
MAX_THREADS = 20  # parallel threads

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

PRODUCT_CONTAINER_SELECTOR = "div.bLCLBY.nr15la"  # main product container
PRODUCT_LINK_SELECTOR = "a[href*='/p/']"  # product link inside container

# --------------------------------------
# SELENIUM DRIVER
# --------------------------------------
def create_driver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--blink-settings=imagesEnabled=false")  # no images

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
    page = 1

    while True:
        print(f"[PAGE] {page}")
        driver.get(BASE_URL.format(page))
        time.sleep(random.uniform(*SCROLL_DELAY))

        # Close login popup if it appears
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, "button._2KpZ6l._2doB4z")
            close_btn.click()
            time.sleep(1)
        except:
            pass

        # Scroll multiple times to load all products
        for _ in range(7):
            driver.execute_script("window.scrollBy(0, 2500)")
            time.sleep(random.uniform(1, 2))

        # Wait for at least one product container
        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_CONTAINER_SELECTOR))
            )
        except:
            print(f"⚠️ No products found on page {page}, stopping.")
            break

        # Collect all product links on this page
        containers = driver.find_elements(By.CSS_SELECTOR, PRODUCT_CONTAINER_SELECTOR)
        new_links = set()
        for c in containers:
            anchors = c.find_elements(By.CSS_SELECTOR, PRODUCT_LINK_SELECTOR)
            for a in anchors:
                link = a.get_attribute("href")
                if link:
                    new_links.add(link)

        # Only add new links
        new_links -= product_links
        if not new_links:
            print("No new links found → finished scraping pages.")
            break

        product_links.update(new_links)
        print(f"Collected so far: {len(product_links)} links")
        page += 1

    driver.quit()
    return list(product_links)

# --------------------------------------
# PHASE 2: SCRAPE PRODUCT DETAILS
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

            # Print progress and save periodically
            if i % 20 == 0 or i == len(links):
                print(f"[PRODUCTS SCRAPED] {i}/{len(links)}")
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
