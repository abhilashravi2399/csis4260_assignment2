
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv("data/articles.csv")
df = df.dropna(subset=["text"]).reset_index(drop=True)
df["title"] = df["title"].fillna("")
print("Articles to analyse:", len(df))


# ---------- Algorithm 1: summary using TF-IDF sentence ranking ----------

# dots in these short forms would confuse the sentence splitter
abbreviations = {"B.C.": "BC", "U.S.": "US", "Mr.": "Mr", "Mrs.": "Mrs",
                 "Ms.": "Ms", "Dr.": "Dr", "St.": "St", "No.": "No"}


def split_sentences(text):
    text = text.replace("\n", " ")
    for short, plain in abbreviations.items():
        text = text.replace(short, plain)
    parts = re.split(r'(?<=[.!?])\s+(?=["“A-Z0-9])', text)
    # ignoring very short fragments such as captions
    return [p.strip() for p in parts if len(p.split()) >= 6]


def summarise(text, n=2):
    sentences = split_sentences(text)
    if len(sentences) <= n:
        summary = " ".join(sentences) if sentences else text[:300]
    else:
        try:
            matrix = TfidfVectorizer(stop_words="english").fit_transform(sentences)
        except ValueError:
            return " ".join(sentences[:n])
        scores = matrix.sum(axis=1).A1.copy()
        scores[0] = scores[0] * 1.3   # news stories put the main point first
        best = sorted(scores.argsort()[-n:])   # keeping the original order
        summary = " ".join(sentences[i] for i in best)
    return re.sub(r"\bBC\b", "B.C.", summary)


df["summary"] = df["text"].apply(summarise)


# ---------- Algorithm 2: relevance using TF-IDF and cosine similarity ----------

topic_query = ("rent rental rents tenants renters landlord eviction vacancy "
               "affordable affordability housing supply student renter Vancouver")

vectoriser = TfidfVectorizer(stop_words="english", sublinear_tf=True)
matrix = vectoriser.fit_transform(df["title"] + " " + df["text"])
query_vector = vectoriser.transform([topic_query])

df["similarity"] = cosine_similarity(query_vector, matrix).ravel()
# scaling so that the most relevant article gets 1.0
df["relevance"] = df["similarity"] / df["similarity"].max()


# ---------- Algorithm 3: direction using a rule-based lexicon ----------
# Each rule is (pattern, weight). Rules are written from the point of view
# of a student renter, so "rents fall" is positive and "eviction" is negative.

positive = [
    (r"\brents?\b[^.]{0,40}\b(drop|drops|dropped|fall|falls|fell|falling|decline|declines|declined|dip|dipped|slow|slows|slowed|ease|eased)\b", 2),
    (r"\b(drop|decline|decrease|dip|fall)s?\b[^.]{0,20}\b(in|of)\b[^.]{0,20}\brents?\b", 2),
    (r"\bmore vacanc", 1.5),
    (r"\bvacancy rates?\b[^.]{0,30}\b(rise|rises|rose|up|increase|increased|higher)\b", 1.5),
    (r"\b(rent|vacancy) control\b", 1.5),
    (r"\b(rent freeze|rent cap|rent ceiling)\b", 1.5),
    (r"\btenant protections?\b", 2),
    (r"\btenants?['’]? rights\b", 1),
    (r"\baffordab\w*", 1),
    (r"\b(new|more) (rental|purpose-built|student|social|affordable) (homes|units|housing|buildings)\b", 2),
    (r"\bpurpose-built rental", 1.5),
    (r"\bhousing (supply|stock)\b[^.]{0,20}\b(grow|growing|grows|increase|increasing|up)\b", 1.5),
    (r"\b(overturn\w*|quash\w*|reject\w*)\b[^.]{0,40}\bevict", 2),
    (r"\bbad faith\b", 1.5),
    (r"\bcompensation\b", 0.5),
]

negative = [
    (r"\brents?\b[^.]{0,40}\b(soar|soars|soared|soaring|surge|surges|surged|jump|jumps|jumped|climb|climbs|climbed|rise|rises|rose|rising|spike|spiked|increase|increases|increased|hike|hikes|hiked)\b", 2),
    (r"\b(increase|rise|hike|jump|spike)s?\b[^.]{0,20}\b(in|of)\b[^.]{0,20}\brents?\b", 2),
    (r"\brent (increase|increases|hike|hikes)\b", 2),
    (r"\bevict\w*", 2),
    (r"\bdisplac\w*", 1.5),
    (r"\b(renoviction|demoviction)s?\b", 2),
    (r"\bshortage\w*", 1.5),
    (r"\bunaffordab\w*", 2),
    (r"\bhomeless\w*", 1),
    (r"\bvacancy rates?\b[^.]{0,30}\b(fall|falls|fell|drop|dropped|low|lower|tight)\b", 1.5),
    (r"\bfewer (rental|units|homes|rooms)\b", 1.5),
    (r"\b(most expensive|highest in the country|record high|new high|highest rents?)\b", 1.5),
    (r"\bwait-?lists?\b", 1),
    (r"\bhousing starts\b[^.]{0,30}\b(down|drop|dropped|fall|fell|decline)\b", 1.5),
    (r"\bfierce competition\b", 1.5),
]


def lexicon_score(text, rules, cap=3):
    # a rule can count at most 3 times, so one repeated phrase does not dominate
    total = 0
    for pattern, weight in rules:
        hits = len(re.findall(pattern, text, flags=re.IGNORECASE))
        total += weight * min(hits, cap)
    return total


def direction(row):
    # headline counts three times because it states the main point
    pos = lexicon_score(row["text"], positive) + 3 * lexicon_score(row["title"], positive)
    neg = lexicon_score(row["text"], negative) + 3 * lexicon_score(row["title"], negative)
    # the +4 keeps the value small when there are only a few matches
    return pd.Series({"pos_points": pos, "neg_points": neg,
                      "direction": (pos - neg) / (pos + neg + 4)})


df = pd.concat([df, df.apply(direction, axis=1)], axis=1)

# importance score from -10 (very bad for a student renter) to +10 (very good)
df["score"] = (10 * df["relevance"] * df["direction"]).round(1)


def label(s):
    if s >= 1:
        return "positive"
    if s <= -1:
        return "negative"
    return "neutral or low impact"


df["label"] = df["score"].apply(label)
df = df.sort_values("date", ascending=False).reset_index(drop=True)

# ---------- Saving the results ----------

df["relevance"] = df["relevance"].round(2)
out = df[["url", "summary", "score", "date", "title", "relevance", "label"]]
out.to_csv("data/results.csv", index=False, encoding="utf-8")

# a markdown table that can be pasted into the README
with open("data/results_table.md", "w", encoding="utf-8") as f:
    f.write("| Date | Title | Score | Label |\n|---|---|---|---|\n")
    for _, r in out.iterrows():
        f.write(f"| {r['date']} | {r['title'].replace('|', '/')} | {r['score']} | {r['label']} |\n")

# ---------- Printing a short report ----------

pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 70)
print("\nLabel counts:")
print(out["label"].value_counts())
print("\nMost positive:")
print(out.nlargest(5, "score")[["date", "title", "score"]].to_string(index=False))
print("\nMost negative:")
print(out.nsmallest(5, "score")[["date", "title", "score"]].to_string(index=False))
print("\nClosest to zero:")
closest = out.reindex(out["score"].abs().sort_values().index).head(5)
print(closest[["date", "title", "score"]].to_string(index=False))
print("\nSaved: data/results.csv and data/results_table.md")