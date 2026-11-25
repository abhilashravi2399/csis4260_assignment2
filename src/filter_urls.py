# Keeps only the recent candidate articles, so the data matches
# the current rental market and the page layouts are similar.

import csv
from collections import Counter

cutoff = "2023-01-01"   # keeping articles from this date onwards

rows = []
with open("data/candidate_urls.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print("Candidates before the date filter:", len(rows))

# how many articles came from each year
years = Counter(row["date"][:4] for row in rows)
for year in sorted(years):
    print(year, ":", years[year])

# dates are written as yyyy-mm-dd, so comparing them as text works fine
recent = [row for row in rows if row["date"] >= cutoff]
print("\nCandidates from", cutoff, "onwards:", len(recent))

# a quick look at the first 15 titles, to check they make sense
print("\nFirst 15 titles:")
for row in recent[:15]:
    print(row["date"], "|", row["title"][:70])

with open("data/selected_urls.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "title", "description", "url"])
    writer.writeheader()
    writer.writerows(recent)

print("\nSaved to data/selected_urls.csv")