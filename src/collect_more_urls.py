# Runs several CBC searches, keeps recent articles only, and merges them into one list

import csv
import re
import time
import requests
from datetime import datetime

url = "https://www.cbc.ca/graphql"
cutoff = "2023-01-01"   # keeping articles from this date onwards
max_pages = 8           # safety limit for each search

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
}

query_template = """query AllSearchItems($searchQuery: String!) {
  allSearchItems(query: $searchQuery, section: "news", contentType: "", sort: "newest", page: PAGE_NUMBER, target: WEB, boosts: ["title^5","description","tags.generic^7"], var: "A") {
    nodes {
      sourceId
      contentType
      title
      description
      url
      publishedAt
    }
    totalCount
  }
}"""

# the different words we will search for
searches = [
    "rent Vancouver",
    "tenants B.C.",
    "eviction Vancouver",
    "rental housing Metro Vancouver",
    "rent increase B.C.",
    "Residential Tenancy Branch",
]

# whole words only, so "current" will not match "rent"
topic_words = re.compile(
    r"\b(rent|rents|rental|rentals|renter|renters|tenant|tenants|tenancy|"
    r"evict\w*|landlord\w*|housing|vacanc\w*|afford\w*|rtb)\b",
    re.IGNORECASE,
)

# places that show the story is about B.C. or Metro Vancouver
places = ["b.c.", "british columbia", "vancouver", "burnaby", "surrey",
          "new westminster", "coquitlam", "kelowna"]


def get_page(search_text, page_number):
    query = query_template.replace("PAGE_NUMBER", str(page_number))
    payload = {"query": query, "variables": {"searchQuery": search_text}}
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()["data"]["allSearchItems"]


all_items = []

for search in searches:
    print("\nSearching for:", search)
    for page in range(1, max_pages + 1):
        try:
            result = get_page(search, page)
        except Exception as e:
            print("  page", page, "failed:", str(e)[:80])
            break

        nodes = result["nodes"]
        if not nodes:
            break

        # converting the publish time from milliseconds to a normal date
        for item in nodes:
            ms = int(item["publishedAt"])
            item["date"] = datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")
        all_items.extend(nodes)

        oldest = min(item["date"] for item in nodes)
        print("  page", page, "| oldest date on page:", oldest)

        # results come newest first, so older pages are not needed
        if oldest < cutoff:
            break
        time.sleep(1)  # one second pause between requests

# removing repeats, because the same article can come from two searches
seen = set()
unique_items = []
for item in all_items:
    if item["url"] not in seen:
        seen.add(item["url"])
        unique_items.append(item)

# keeping recent stories that are about renting or housing in B.C.
selected = []
for item in unique_items:
    text = ((item["title"] or "") + " " + (item["description"] or "")).lower()
    in_bc = "british-columbia" in item["url"] or any(p in text for p in places)
    if (item["contentType"] == "story" and item["date"] >= cutoff
            and topic_words.search(text) and in_bc):
        selected.append(item)

selected.sort(key=lambda x: x["date"], reverse=True)

with open("data/selected_urls.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "title", "description", "url"])
    for row in selected:
        writer.writerow([row["date"], row["title"], row["description"], row["url"]])

print("\nUnique articles collected:", len(unique_items))
print("Recent articles about renting or housing in B.C.:", len(selected))
print("\nFirst 10 titles:")
for row in selected[:10]:
    print(row["date"], "|", row["title"][:70])
print("\nSaved to data/selected_urls.csv")