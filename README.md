CSIS 4260: Assignment 2, Web Scraping and Text Analysis

Student: Abhilash Ravindranathan
Program: Computer and Information Systems Post-Baccalaureate, Douglas College
Topic: Rental housing in Metro Vancouver, as reported by CBC News

1. Overview

This project scrapes news articles about rental housing from CBC News, summarises each article, and gives each one an importance score with a direction (positive or negative). It has two parts.

Part 1, web scraping: two libraries were compared with a small benchmark, one was chosen, and it was used to collect full-text articles.
Part 2, text analysis: three algorithms were applied to the scraped text to produce a summary, a relevance value and a signed importance score for every article.

The final deliverable is data/results.csv, which has the url, summary and score of every article (plus date, title, relevance and label as extra columns).

2. Topic and viewpoint

I chose rental housing in Metro Vancouver because it is something I deal with directly as a student. Rent in this region is very high, and finding a decent room or small flat near college is a real worry for me and for many of my classmates. Because I know the problem first-hand, I could judge whether a news story is good or bad for a renter with some confidence instead of guessing.

A score can only be positive or negative for someone, so every score in this project is measured from the point of view of a student renting a room or small flat near Douglas College.

Direction	Meaning for a student renter	Examples
Positive	Renting becomes easier or cheaper	Falling asking rents, new purpose-built rentals, student housing, stronger tenant protection
Negative	Renting becomes harder or more expensive	Rent increases, evictions, falling vacancy rates, housing shortage
Close to zero	Housing news that hardly touches a student renter	Property sales, stadium or arena projects, stories from other provinces
3. Project structure
csis4260_assignment2/
  src/
    benchmark.py           compares requests + BeautifulSoup with Playwright
    test_urls.txt          five test links used by the benchmark
    collect_urls.py        first attempt: every result of one search, kept for reference
    collect_more_urls.py   runs six CBC searches and saves the recent article links
    scrape_articles.py     downloads the full text of each article
    analyze_articles.py    summary, relevance, direction and importance score
  data/
    all_search_results.csv   output of the first attempt (all 274 results of one search)
    candidate_urls.csv       output of the first attempt after a keyword filter
    selected_urls.csv        links chosen for scraping (recent and on topic)
    articles.csv             scraped articles with full text
    results.csv              FINAL OUTPUT: url, summary, score, date, title, relevance, label
    results_table.md         the same results as a markdown table
  requirements.txt
  README.md
  .gitignore               keeps the virtual environment out of the repository
4. How to run the code

The code was written and tested on Windows with Python 3 inside a virtual environment. Run every command from the main project folder, not from inside src.

Step 1: create and activate a virtual environment

python -m venv venv
venv\Scripts\Activate.ps1          (Windows PowerShell)
source venv/bin/activate           (Mac or Linux)

Step 2: install the dependencies

pip install -r requirements.txt

Step 3: run the pipeline in this order

python src/collect_more_urls.py
python src/scrape_articles.py
python src/analyze_articles.py
Script	What it does	Approximate time
collect_more_urls.py	Collects recent article links and writes data/selected_urls.csv	1 minute
scrape_articles.py	Downloads the article text and writes data/articles.csv	4 minutes
analyze_articles.py	Writes data/results.csv and data/results_table.md	a few seconds

Optional: the library benchmark. It needs the browser used by Playwright, which is a separate download.

playwright install chromium
python src/benchmark.py

scrape_articles.py has a variable called LIMIT near the top. In the submitted version it is set to 3, so the current data/articles.csv contains only the first three selected articles. When LIMIT is a number (for example 3) the script runs in test mode and scrapes only that many articles. For the full run it must be None. After scraping all selected URLs, rerun analyze_articles.py to regenerate the full results.csv and results_table.md.

Cost: no paid API is used. Everything runs locally with free libraries, so the total cost was $0, well inside the $5 limit.

5. Part 1: Web scraping
5.1 Library comparison

Two libraries were compared on the same five CBC News articles about rental housing. Both used the same browser-style user agent, the same one-second pause between pages and the same text extraction code, so the comparison was fair.

requests + BeautifulSoup downloads the raw HTML and reads it.
Playwright opens a real (hidden) Chromium browser, so JavaScript runs as it would for a normal visitor.

Scrapy was not tested. It is built for large crawls and needs a full project structure, which is too much for about a hundred pages.

	requests + BeautifulSoup	Playwright
Pages loaded successfully	5 out of 5	0 out of 5
Total time for 5 pages	9.0 seconds	144.9 seconds
Article text found	3,763 to 7,222 characters per page	nothing
Setup	one pip install	pip install plus a separate browser download
Ease of use	very simple, a few lines of code	more code, and slower to run and debug

requests + BeautifulSoup worked on the first attempt. Playwright first failed with ERR_HTTP2_PROTOCOL_ERROR. After I disabled HTTP/2, changed the user agent and waited only for the page structure to load, it still failed on every page, with ERR_CONNECTION_RESET once and timeouts on the other four.

I do not know for certain why CBC refused the automated browser. It may be bot detection, or it may be something on my network. Either way, the result was the same on every page.

5.2 Library chosen: requests + BeautifulSoup

I chose requests + BeautifulSoup for these reasons:

It loaded all five test pages, while Playwright loaded none.
It was about sixteen times faster in the benchmark (9.0 s against 144.9 s).
CBC article text is already present in the plain HTML, so a full browser that runs JavaScript is not needed for this site.
It has fewer moving parts, which makes the code easier to read, debug and explain.
5.3 How the articles were collected

Finding the links. The CBC search page fills in its results using JavaScript, so a plain request to the page returned an almost empty result. An RSS feed was also tried, but it only holds the newest stories and almost none were about rent. I then used the browser developer tools (Network tab, Fetch/XHR filter) and found that the search page asks https://www.cbc.ca/graphql for its results as JSON. The script collect_more_urls.py sends the same request, with the page number changed for each page.

Choosing the articles. A single search ("rent Vancouver") returned 274 results, but most were old. Only 25 were from 2023 onwards. To get enough recent articles, collect_more_urls.py runs six searches and merges the results:

rent Vancouver
tenants B.C.
eviction Vancouver
rental housing Metro Vancouver
rent increase B.C.
Residential Tenancy Branch

After removing repeats, an article is kept only if it is a news story, was published in 2023 or later, mentions renting or housing in its headline or description (matched as whole words, so "current" does not match "rent"), and is connected to B.C. through its web address or a place name. I used 2023 as the cut-off because older articles do not describe today's rental market, and older CBC pages sometimes have a different layout. The submitted files contain 274 unique search results in all_search_results.csv, 196 keyword-matched entries in candidate_urls.csv, and 94 recent entries in selected_urls.csv. The 94 is the final selected URL count, not the count in candidate_urls.csv.

Downloading the text. scrape_articles.py downloads each article page, finds the article container, and joins its paragraphs. Paragraphs inside captions, side boxes and footers are skipped.

Two problems were found during a 3-article test run and fixed before the full run:

The first letter of some articles was split from the rest of the word ("T he latest analysis"), because CBC styles it separately. The fix was to join the text without a separator and then tidy the spaces.
Some articles ended with a link to another story. This is not part of the article, so paragraphs made only of a link are now skipped.

Failed downloads are retried once, and any that still fail are listed in the output.

5.4 Responsible scraping
robots.txt: The submitted project files do not include a saved copy or exact excerpt of CBC's robots.txt. Therefore, the applicable rule for /graphql cannot be verified from the evidence provided, and I have not guessed what it says. Check the current https://www.cbc.ca/robots.txt and record the exact applicable directive before stating that this endpoint is permitted.
Rate limiting: the scripts pause for one to one and a half seconds between requests.
Volume: only a few hundred requests were made in total.
Identification: a normal browser user agent was used.
Use of the data: the articles were collected only for this coursework. The text is not republished, and only short summaries are included in the results.
5.5 Scraping result
Candidate articles selected: 94 (rows in data/selected_urls.csv)
Articles scraped successfully: 3 (rows in data/articles.csv)
Failed pages: Not recorded in the submitted files. The scraper is currently set to LIMIT = 3, so this is a three-article test run, not a full scrape of all 94 selected URLs. The three saved article records confirm three successful extractions; the original console summary needed to verify the exact failure count was not included.

6. Part 2: Text analysis

Three algorithms were used. All of them are free and run locally.

6.1 Algorithm 1: summary with TF-IDF sentence ranking
The article is split into sentences. Short forms such as "B.C." are protected so that they do not end a sentence, and fragments shorter than six words (such as captions) are ignored.
TF-IDF is calculated for the sentences of that article. A sentence scores higher when it has more distinctive words, meaning words that are frequent in the article but not spread through every sentence.
The first sentence gets a 30% boost, because a news story normally states its main point at the start.
The two highest-scoring sentences are returned in their original order as the summary.

This is an extractive summary: it picks existing sentences and does not write new ones. That keeps every summary faithful to the article and costs nothing.

6.2 Algorithm 2: relevance with TF-IDF and cosine similarity

The topic is described with a short list of words: rent, rental, rents, tenants, renters, landlord, eviction, vacancy, affordable, affordability, housing, supply, student, renter, Vancouver. Every article (headline plus text) is converted to a TF-IDF vector, and its cosine similarity to the topic vector is measured. The values are then divided by the highest value, so the most relevant article gets 1.0 and an unrelated article, such as one about a sports arena, gets a value close to 0.

This is what gives the score its size. An article that is mostly about rent can get a large score, while a story that only mentions rent once cannot.

6.3 Algorithm 3: direction with a rule-based lexicon

Plain sentiment tools are a poor fit here, because "rents drop" sounds negative to a general sentiment model but is good news for a renter. So the direction comes from about 30 hand-written patterns, 15 positive and 15 negative, all written from a student renter's point of view.

Positive rules (examples)	Negative rules (examples)
rents drop, fall, decline or slow	rents soar, surge, rise or jump
more vacancies, higher vacancy rate	eviction, displacement, renoviction
tenant protections, rent freeze or cap	housing shortage, unaffordable
new rental or student housing	highest in the country, record high
court overturns an eviction, bad faith finding	fewer rental units, long wait-lists

Each rule has a weight between 0.5 and 2. To stop one repeated phrase from taking over, a rule can count at most three times per article. A match in the headline counts three times, because the headline states the main point.

6.4 How the importance score is calculated
direction = (positive points - negative points) / (positive points + negative points + 4)
score     = 10 x relevance x direction
direction lies between -1 and +1. The +4 in the denominator keeps it small when there are only one or two matches, so a weak signal cannot produce an extreme score.
relevance lies between 0 and 1 (Algorithm 2).
score therefore lies between -10 (very bad for a student renter) and +10 (very good).
Score	Label
+1 or more	positive
-1 or less	negative
between -1 and +1	neutral or low impact

Worked example (illustrative numbers, not a real article): an article with relevance 0.90, 4 positive points and 10 negative points has direction (4 - 10) / (4 + 10 + 4) = -0.33, so its score is 10 x 0.90 x -0.33 = -3.0, which is labelled negative.

6.5 Why these methods
No paid API. The assignment allows commercial or LLM APIs within a $5 budget, but classical methods are free, reproducible, and easy to explain and inspect. Anyone can re-run the code and get the same numbers.
Separating size from sign. Relevance gives the size and the lexicon gives the sign, so a story that is about housing but not about renting stays close to zero.
Transparency. Every score can be traced to the patterns that matched, which made it easy to find and fix mistakes.
7. Results

The generated table is in data/results.csv (columns: url, summary, score, date, title, relevance, label). A markdown version with date, title, score and label is in data/results_table.md.

| Result category | Number of articles |
|---|---:|
| Positive (score of +1 or more) | 2 |
| Negative (score of -1 or less) | 0 |
| Neutral or low impact | 1 |
| **Total analysed** | **3** |

Most positive articles:
- **Average asking rent down 2.9% in B.C. in September, marking 2 years of decreases: report** — **+5.5** (relevance 1.00)
- **Asking rents drop again, but B.C. remains among Canada's most expensive markets** — **+3.1** (relevance 0.98)

Most negative articles: None. No article in this three-article test dataset received a score of -1 or lower. The lowest score was 0.0.

Close to zero:
- **Vancouver Giants to move to Surrey as city announces 10,000-seat arena** — **0.0** (relevance 0.24). This is an arena story rather than a rental-market story, so its low relevance and neutral score are consistent with the project's student-renter viewpoint.

These figures were generated by running src/analyze_articles.py against the three article records in data/articles.csv. They describe the current test dataset only, not all 94 selected URLs.

7.1 Spot check

A documented manual spot-check count and notes were not included in the submitted files, so I cannot state how many articles were manually read or claim that the results were independently validated. The automated results are consistent with the rule definitions for this small sample: the two articles reporting falling rents received positive scores, while the unrelated arena story received a score of 0.0. This is an automated consistency observation, not a substitute for manual review.

8. Limitations
Keyword rules cannot read context. The direction comes from patterns, so it can miss sarcasm, quotations from people who disagree, and stories that carry good and bad news together. An article about a court cancelling an eviction mentions "evict", which is a negative word, so a special rule was added for that case, but similar cases may still be missed.
The word lists reflect one viewpoint. They were written for a student renter. A landlord or a home buyer would flip the sign of many rules, for example falling rents.
One news source. All articles come from CBC News, so the results show CBC's coverage and not the whole rental market.
Loose first filter. The keyword filter in the collection step lets a few off-topic stories through. The relevance score pushes those towards zero, but they remain in the data.
Extractive summaries. The summaries use two original sentences, so they can feel slightly abrupt and may miss a point that is spread across several sentences.
Scores are not validated against human labels. Apart from the spot check above, there is no ground truth to measure accuracy.
9. Possible improvements
Compare the lexicon scores with scores from a small manual labelling of 30 articles, and report agreement.
Replace or support the lexicon with a language model for the direction, keeping the cost under the $5 limit.
Add more news sources, such as Global News BC, to reduce dependence on one outlet.
Tune the pattern weights using the manually labelled articles.
10. Reproducibility notes
The articles were scraped in November 2026. CBC may add, change or remove articles, so a later run can give a slightly different list and different scores.
requirements.txt lists the exact library versions used. The virtual environment folder (venv/) is not part of the repository and is ignored through .gitignore.
All scripts print their progress, so each step can be checked as it runs.