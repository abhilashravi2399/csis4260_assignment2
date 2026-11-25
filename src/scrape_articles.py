# Downloads the full text of each selected CBC article.


import csv
import time
import requests
from bs4 import BeautifulSoup

# TEST MODE: only the first 3 articles. Change to None for the full run.
LIMIT = 3

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# places where the article text might sit, tried in this order
containers = ["div.story", "[data-cy='storyWrapper']", "article", "main"]


def extract_text(soup):
    # trying each container until one gives a reasonable amount of text
    for selector in containers:
        box = soup.select_one(selector)
        if box is None:
            continue
        paragraphs = []
        for p in box.find_all("p"):
            # skipping paragraphs inside captions, side boxes and footers
            if p.find_parent(["figure", "aside", "footer", "nav"]):
                continue
            text = p.get_text(" ", strip=True)
            if text:
                paragraphs.append(text)
        body = "\n".join(paragraphs)
        if len(body) > 500:
            return body, selector
    return "", "none"


def scrape_one(url):
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code != 200:
        return None, r.status_code, "none"
    soup = BeautifulSoup(r.text, "lxml")
    body, method = extract_text(soup)
    return body, r.status_code, method


# reading the list made in the last step
with open("data/selected_urls.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

if LIMIT:
    rows = rows[:LIMIT]

print("Articles to scrape:", len(rows))

results = []
failed = []

for i, row in enumerate(rows, start=1):
    try:
        body, status, method = scrape_one(row["url"])
        if body is None:
            # one more try after a short wait
            time.sleep(3)
            body, status, method = scrape_one(row["url"])
    except Exception as e:
        body, status, method = None, "error", str(e)[:40]

    if body:
        row["text"] = body
        row["characters"] = len(body)
        row["method"] = method
        results.append(row)
        print(i, "| ok |", method, "|", len(body), "characters |", row["title"][:45])
    else:
        failed.append((row["url"], status, method))
        print(i, "| FAILED |", status, "|", row["title"][:45])

    time.sleep(1.5)  # pause between pages, so we are polite to the site

with open("data/articles.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=["date", "title", "description", "url", "text", "characters", "method"]
    )
    writer.writeheader()
    writer.writerows(results)

print("\nScraped:", len(results), "| Failed:", len(failed))
for item in failed:
    print("  failed:", item)

# in test mode, showing the start and end of each article to check them
if LIMIT:
    for row in results:
        print("\n==========", row["title"])
        print("START:", row["text"][:300])
        print("END:", row["text"][-250:])