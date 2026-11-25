# Compares requests + BeautifulSoup with Playwright on the same CBC pages.

import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# reading the test links, one link per line
with open("src/test_urls.txt") as f:
    urls = [line.strip() for line in f if line.strip()]

# same user agent for both libraries, so the comparison is fair
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
headers = {"User-Agent": user_agent}


def get_title_and_body(html):
    # same extraction logic for both libraries
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else ""
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    body = " ".join(paragraphs)
    return title, body


def show_results(name, results, total_time):
    print("\n---", name, "---")
    for row in results:
        print("status:", row[0], "| title:", row[1], "| body characters:", row[2])
    print("Total time (seconds):", round(total_time, 1))


def run_requests_bs4(urls):
    results = []
    start = time.time()
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            title, body = get_title_and_body(r.text)
            results.append((r.status_code, title[:40], len(body)))
        except Exception as e:
            # keeping the error so it shows in the table
            results.append(("error", str(e)[:40], 0))
        time.sleep(1)  # small delay so we do not hit the site too fast
    return results, time.time() - start


def run_playwright(urls):
    results = []
    start = time.time()
    with sync_playwright() as p:
        # --disable-http2 avoids the ERR_HTTP2_PROTOCOL_ERROR we got earlier
        browser = p.chromium.launch(headless=True, args=["--disable-http2"])
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        for url in urls:
            try:
                response = page.goto(url, timeout=30000, wait_until="domcontentloaded")
                html = page.content()
                title, body = get_title_and_body(html)
                results.append((response.status, title[:40], len(body)))
            except Exception as e:
                results.append(("error", str(e)[:40], 0))
            time.sleep(1)  # same delay as the other method
        browser.close()
    return results, time.time() - start


print("Running requests + BeautifulSoup...")
bs_results, bs_time = run_requests_bs4(urls)
show_results("requests + BeautifulSoup", bs_results, bs_time)

print("\nRunning Playwright...")
pw_results, pw_time = run_playwright(urls)
show_results("Playwright", pw_results, pw_time)