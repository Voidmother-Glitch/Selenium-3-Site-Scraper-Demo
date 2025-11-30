import subprocess
import sys
import time
import random
import re
import threading

# === PRE-FLIGHT PACKAGE CHECK ===
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from concurrent.futures import ThreadPoolExecutor
except ImportError as e:
    print("WARNING: You're missing required packages!")
    print("Please install 'selenium'.")
    print("User consent required to install.")
    print()

    choice = input("Install selenium now? (y/n): ").strip().lower()
    if choice not in ['y', 'yes']:
        print("\nINSTALLATION CANCELLED. HOW RUDE. Please install manually:")
        print("    pip install selenium")
        exit(1)

    print("\nINSTALLING SELENIUM... please wait.")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        print("SELENIUM INSTALLED SUCCESSFULLY!")
        print("Restarting script...")
        print("-" * 50)
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except Exception as install_error:
        print(f"\nINSTALLATION FAILED! Sadface!: {install_error}")
        print("Please install manually!")
        print("    pip install selenium")
        exit(1)

# === SELENIUM OPTIMIZATIONS ===

# Chrome options for max speed
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-images")  # Disable images
chrome_options.add_argument("--disable-css")     # Disable CSS (if possible)
#chrome_options.add_argument("--disable-javascript")   Disables JS, not in use as this engagement uses JS validation
chrome_options.add_argument("--disable-web-security")  # Disable CORS
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
chrome_options.add_argument("--disable-features=TranslateUI")
chrome_options.add_argument("--disable-features=Translate")
chrome_options.add_argument("--disable-features=AutofillServerCommunication")

# Create a pool of browser instances (this will be reusing them)
BROWSER_POOL = []
MAX_BROWSERS = 10  # Adjust based on your system RAM, only 10 for testing purposes

for _ in range(MAX_BROWSERS):
    driver = webdriver.Chrome(options=chrome_options)
    BROWSER_POOL.append(driver)

# === SCRAPE FUNCTION ===
def scrape_page(url):
    # Get a browser from the pool (thread-safe)
    driver = BROWSER_POOL.pop(0)
    try:
        driver.get(url)
        # Wait for page to load (adjust timeout as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Get page source
        html = driver.page_source

        # Extract MD5 hash (32-character hex string)
        md5_match = re.search(r'[a-fA-F0-9]{32}', html)
        md5_hash = md5_match.group(0) if md5_match else "NOT_FOUND"

        return {
            'url': url,
             # Selenium doesn't return HTTP status, so we cannot retrieve an HTTP request code.
            'md5_hash': md5_hash,
        }

    except Exception as e:
        return {
            'url': url,
            'md5_hash': 'ERROR',
            'error': str(e)
        }
    finally:
        # Return browser to pool
        BROWSER_POOL.append(driver)

# === MAIN FUNCTION ===
def main():
    print("Please provide three target sites!")
    sites = []
    for i in range(3):
        url = input(f"Site {i+1}: ").strip()
        sites.append(url)

    # Define range of numbers to scrape
    start_num = 0
    total_pages = 20  # Adjust as needed, only 20 for testing purposes

    # Shuffle the order of page numbers to avoid predictable patterns
    page_numbers = list(range(total_pages))
    random.shuffle(page_numbers)

    # Create list of URLs
    urls = []
    for i in page_numbers:
        site_index = i % 3
        number = start_num + i
        url = f"{sites[site_index]}/scraping/{number}"
        urls.append(url)

    print(f"STARTING SELENIUM SCRAPE OF {len(urls)} PAGES BUT WE BEIN' SNEAKY...")
    start_time = time.time()

    # Use ThreadPoolExecutor to scrape multiple pages concurrently
    results = []
    with ThreadPoolExecutor(max_workers=MAX_BROWSERS) as executor:  # Use MAX_BROWSERS as max_workers
        futures = [executor.submit(scrape_page, url) for url in urls]
        for future in futures:
            results.append(future.result())

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"SCRAPED {len(results)} PAGES IN {elapsed:.2f} SECONDS ({len(results)/elapsed:.0f} PAGES/SEC)")

    # === OUTPUT TO FILE ===
    output_file = "scrape_results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== COLLECTED DATA ===\n")
        for item in results:
            f.write(f"URL: {item['url']}\n")
            #f.write(f"Status: {item['status_code']}\n")
            f.write(f"MD5: {item['md5_hash']}\n")
            f.write("-" * 50 + "\n")

    print(f"\nALL DATA SAVED TO: {output_file}")

    # Optional: Print first 10 results to console
    print("\n=== FIRST 10 RESULTS ===")
    for item in results[:10]:
        print(f"URL: {item['url']}")
        #print(f"Status: {item['status_code']}")
        print(f"MD5: {item['md5_hash']}")
        print("-" * 50)

    # Close all browsers
    for driver in BROWSER_POOL:
        driver.quit()

# === RUN SCRIPT ===
if __name__ == "__main__":
    main()