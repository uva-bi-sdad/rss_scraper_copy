# dspg22_rss-scraper

Description
---
- A toolbox of scripts to retrieve rss data as well as the news article text via keywords and time ranges
- _rss-get.py_ retrieves rss feeds given keywords and time ranges and saves to an output directory
- _news-get.py_ takes inputs of a csv or a directory of csvs with a url column and appends a new column with the specified text

rss-get
===
To use
---
```python
usage: rss-get.py [-h] -k KEYWORDS [KEYWORDS ...] [-s SOURCES [SOURCES ...]] [-o OUTDIR] [-sd START_DATE] [-ed END_DATE]
                  [-v | --verbose | --no-verbose]

DSPG pull from RSS sources

options:
  -h, --help            show this help message and exit
  -k KEYWORDS [KEYWORDS ...], --keywords KEYWORDS [KEYWORDS ...]
                        Keywords to parse
  -s SOURCES [SOURCES ...], --sources SOURCES [SOURCES ...]
                        Sources (['google', 'bing']) to parse from. If None, parses all possible sources
  -o OUTDIR, --outdir OUTDIR
  -sd START_DATE, --start_date START_DATE
                        Start date of the search in Y-m-d format. If none and end date provided, or if provided date further than
                        now, raises error
  -ed END_DATE, --end_date END_DATE
                        End date of the search in Y-m-d format. If none provided, uses the current time
  -v, --verbose, --no-verbose
```

Examples
---
Run a search on the keywords ```apples, oranges, bananas```, and export the csvs to the output directory "output":

```shell
python rss-get.py -k apples oranges bananas -o output
```

Run a search on the keywords ```apple``` for everything after March 3rd, 2022 without saving in verbose mode (note _Bing_ does not have time-based searches)
```shell
python rss-get.py -k apples -sd 2022-03-03 -v
```

Run a search on the keywords ```apple, bananas, oranges``` for everything after March 14th, 2021 only using google
```shell
python rss-get.py -k apples bananas oranges -sd 2021-03-14 -s google
```

Sources check list
---
- _Completion_ is defined as **C**omplete and **V**isited

Completion|**Source**|**Type**|**Keyword**|**Snippet**|**Notes**|
|--|--|--|--|--|--|
|C|[Google](https://news.google.com/rss/search?q={0})|Search Engine|Y|Y|<ul><li>Successful RSS keyword extraction using: https://news.google.com/rss/search?q={0}</li><li>Column _summary_detail.value_ might contain one sentence description of the news</li></ul>|
|C|[Bing](https://www.bing.com/news/search?q={0}&format=rss)|Search Engine|Y|Y|<ul><li>Successful RSS keyword extraction using: https://www.bing.com/news/search?q={0}&format=rss</li><li>Column _summary_detail.value_ might contain 2-3 sentences of the news </li></ul>|
|V|[Baidu](?)|Search Engine|N|N|<ul><li>I found a website https://www.baidu.com/search/rss.html that seems to describe the existance of rss functioning. However, upon clicking into the keyword search field, I kept being returned the same news in non-RSS format</li></ul>|
|V|[Yahoo News](https://news.yahoo.com/rss)|News Channel|N|N|<ul><li>Does not seem to allow keyword searches. If you do a yahoo search with news it automatically returns search.yahoo.com.</li><li>You can manipulate the [URL](https://news.search.yahoo.com/search;_ylt=A2KIbMuIVJpipzUAhiNXNyoA;_ylu=Y29sbwNiZjEEcG9zAzEEdnRpZAMEc2VjA3Nj?p={KEYWORD}&fr=news) to do news page sources, but it does not seem like they will convert it into an RSS format for us </li></ul>
|V|[Yandex](https://yandex.com/)|Search Engine|N|N|<ul><li>robots.txt disallows /company/*.rss, /company/search. Returns results in Russian?</li><li>Upon searching [sitemaps](https://yandex.com/support/sitemap.xml), found an rss source at [https://zen.yandex.ru/](https://zen.yandex.ru/search?query={0}). However, to subscribe to any of the feeds require signing in</li></ul>|
|V|[Ask](https://www.ask.com/rss)|Search Engine|N|Y| <ul><li> Found https://www.ask.com/rss, but so far haven't found a way to add a keyword. </li> <li> Looked through: https://www.ask.com/sitemap_index.xml and https://www.ask.com/robots.txt but did not find anything rss-related</li><li>Column _metadescription_ contains 2 sentences </ul>|
|C|[ABC News](https://abcnews.go.com)|General Media|Y|N|<ul><li>Does not have usable rss feed. Web scraping with keyword search is possible, but most of the content is videos without transcript. I think we do NOT need to dig any deeper.</li></ul>

---

news-get
===

Challenges
---
We have implemented the text extractor with _newspaper_, but the following sites cannot be reached or scrapped.
|**Site**|**URL**|**Description**|
|--|--|--|
|Barron's|(https://www.barrons.com)|Access denied|
|Wall Street Journal|(https://www.wsj.com)|Access denied|
|Forbes|(https://www.forbes.com)|Access denied|
|Bloomberg|(https://www.bloomberg.com)|Not-a-robot test|
|Reuters|(https://www.reuters.com)|Account required to view full text|


Notes
---
- https://www.overleaf.com/4259256516zdhfhfqcshjj

Acknowledgement
---
This project was built as part of the 2022 [Data Science for the Public Good (DSPG) internship program](https://biocomplexity.virginia.edu/data-science-public-good-internship-program)
