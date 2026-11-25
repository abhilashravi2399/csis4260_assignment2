# Collects CBC article links about rental housing using the same data

import csv
import re
import time
import requests
from datetime import datetime

url = "https://www.cbc.ca/graphql"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
}

# the query copied from the Payload tab, with the page number left open
query_template = """query AllSearchItems($searchQuery: String!) {
  allSearchItems(query: $searchQuery, section: "news", contentType: "", sort: "newest", page: PAGE_NUMBER, target: WEB, boosts: ["title^5","description","tags.generic^7"], var: "A") {
    nodes {
      sourceId
      contentType
      title
      description
      url
      publishedAt
      authors
    }
    totalCount
  }
}"""

# whole words only, so "current" or "parent" will not match "rent"
topic_words = re.compile(
    r"\b(rent|rents|rental|rentals|renter|renters|tenant|tenants|tenancy|"
    r"evict\w*|landlord\w*|housing|vacanc\w*|afford\w*|rtb)\b",
    re.IGNORECASE,
)


def get_page(page_number):
    # putting the page number into the query text
    query = query_template.replace("PAGE_NUMBER", str(page_number))
    payload = {"query": query, "variables": {"searchQuery": "rent Vancouver"}}
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()["data"]["allSearchItems"]


all_items = []
total_count = None
page = 1

while True:
    try:
        result = get_page(page)
    except Exception as e:
        print("Page", page, "failed:", str(e)[:80])
        break

    if total_count is None:
        total_count = result["totalCount"]
        print("CBC says there are", total_count, "results in total")

    nodes = result["nodes"]
    if not nodes:
        break

    all_items.extend(nodes)
    print("Page", page, "| articles so far:", len(all_items))

    # stopping when we have everything CBC reports
    if len(all_items) >= total_count:
        break

    page += 1
    time.sleep(1)  # one second pause between requests

# publishedAt is in milliseconds, so converting it to a normal date
for item in all_items:
    ms = int(item["publishedAt"])
    item["date"] = datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")

# removing repeats, in case the same article comes on two pages
seen = set()
unique_items = []
for item in all_items:
    if item["url"] not in seen:
        seen.add(item["url"])
        unique_items.append(item)

# keeping stories whose title or description is about renting or housing
related = []
for item in unique_items:
    text = (item["title"] or "") + " " + (item["description"] or "")
    if item["contentType"] == "story" and topic_words.search(text):
        related.append(item)


def save_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "title", "description", "url"])
        for row in rows:
            writer.writerow([row["date"], row["title"], row["description"], row["url"]])


save_csv("data/all_search_results.csv", unique_items)
save_csv("data/candidate_urls.csv", related)

print("\nUnique articles collected:", len(unique_items))
print("Articles that look related to renting or housing:", len(related))
if related:
    print("Dates from", related[-1]["date"], "to", related[0]["date"])
print("Saved to data/all_search_results.csv and data/candidate_urls.csv")