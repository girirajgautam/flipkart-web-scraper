from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# -------------------------
# 1️⃣ Setup Chrome
# -------------------------
options = Options()
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# -------------------------
# 2️⃣ Selectors (YOUR REAL CLASSES)
# -------------------------
container_selector = "div.jIjQ8S"
title_selector = "div.RG5Slk"
price_selector = "div.hZ3P6w.DeU9vF"
image_selector = "img.UCc1lI"
link_selector = "a"

# -------------------------
# 3️⃣ Scraping Logic
# -------------------------
data = []
seen_links = set()
page = 1
MAX_PAGES = 25   # increase if needed

while page <= MAX_PAGES:
    print(f"Scraping page {page}...")

    url = f"https://www.flipkart.com/search?q=laptops&page={page}"
    driver.get(url)
    time.sleep(3)

    # Close login popup
    if page == 1:
        try:
            close_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z"))
            )
            close_btn.click()
            time.sleep(2)
        except TimeoutException:
            pass

    products = driver.find_elements(By.CSS_SELECTOR, container_selector)

    if not products:
        print("No products found → stopping")
        break

    for product in products:
        try:
            # Title
            try:
                title = product.find_element(By.CSS_SELECTOR, title_selector).text.strip()
            except:
                title = ""

            # Link
            try:
                link = product.find_element(By.CSS_SELECTOR, link_selector).get_attribute("href")
                if link in seen_links:
                    continue
                seen_links.add(link)
            except:
                link = ""

            # Image
            try:
                image = product.find_element(By.CSS_SELECTOR, image_selector).get_attribute("src")
            except:
                image = ""

            # Price
            try:
                price = product.find_element(By.CSS_SELECTOR, price_selector).text.strip()
            except:
                price = ""

            if title and link:
                data.append({
                    "title": title,
                    "price": price,
                    "image": image,
                    "link": link
                })

        except:
            continue

    page += 1

# -------------------------
# 4️⃣ Save to Excel
# -------------------------
df = pd.DataFrame(data)
df.to_excel("flipkart_products_all_pages.xlsx", index=False)

print(f"\n✅ Scraped {len(data)} products successfully")
driver.quit()
