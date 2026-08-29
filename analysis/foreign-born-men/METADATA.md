# Publishing metadata — "The Men Who Vanished"

Everything Prismic needs for this post. Drafted 2026-08-29.

Replace the `REPLACE_ME` value before publishing: the Prismic image delivery URL
for the hero. Confirm the `/p/` slug matches what Prismic assigns.

---

## Email

**Subject:** 2.1 million men are missing from the jobs data

**Preview text** (79 chars — first 39 survive mobile truncation):

> They did not stop looking for work. Eighty-eight percent came straight out of jobs.

Do not lead the preview with "foreign-born." The finding is the mechanism —
people leaving the count from *employment* rather than drifting into
not-in-the-labor-force — and a nativity label in the first 39 characters gets the
post sorted into a political bucket before the mechanism is read.

---

## Title

**Use this** (57 chars — fits Google's ~60 char display):

> The Men Who Vanished: 2.1 Million Gone From the Jobs Data

Alternatives:

| Angle | Title | Chars |
|---|---|---:|
| Search-first | Foreign-Born Men Drive the Entire U.S. Labor Force Decline | 58 |
| Mechanism-first | They Didn't Quit Looking for Work. They Stopped Being Counted. | 62 |

The email subject and the SEO title should differ. The subject sells the open;
the title has to survive a search results page.

---

## Meta description

**Use this** (156 chars):

> The foreign-born male population has fallen 2.1 million across two summers — the two steepest on record. 88% came straight out of employment, not the sidelines.

Alternative (152 chars), leading with the labor force framing:

> Foreign-born workers are 19% of the labor force and 92% of its shortfall. Native-born men came in above a typical summer, not below. Nobody filled the gap.

---

## Meta keywords

```
foreign born labor force, foreign born population, immigration labor market,
Bureau of Labor Statistics, BLS, Current Population Survey, CPS, labor force
participation, native born workers, employment population ratio, labor supply,
jobs report, July 2026 jobs report, labor shortage, economic data
```

**Worth knowing:** Google has ignored the `<meta name="keywords">` tag since
2009 and it carries no ranking weight. It is included because Prismic exposes
the field and because some internal site searches, syndication partners, and
non-Google engines still read it. The `keywords` property inside the JSON-LD
below is the one that does modern work.

---

## Alt text

**hero_foreign_born_men.png**

> Line chart of the foreign-born male population of the United States from 2007
> to July 2026, in millions. The line rises from about 17.3 million in 2007 to
> about 25.0 million in early 2025, then falls to 22.8 million by July 2026. Two
> segments are highlighted: January to July 2025, a fall of 1.2 million, and
> January to July 2026, a fall of 0.9 million.

**chart_ranking.png**

> Bar chart of the change in the foreign-born male population from January to
> July, for every year from 2007 to 2026. 2025 is the steepest decline at
> 1,170,000 and 2026 is second at 919,000. The third steepest is 2020 at 336,000.
> Most other years fall between negative 100,000 and positive 550,000.

**chart_where_they_went.png**

> Grouped bar chart comparing the change in foreign-born men by labor force
> status across the summers of 2025 and 2026 against a typical pair of summers.
> Employment normally rises 835,000 but instead fell 971,000. Unemployment fell
> 464,000 against a typical 475,000, and the number not in the labor force fell
> 653,000 against a typical 401,000.

**chart_not_filled.png**

> Grouped bar chart comparing the change in native-born men across the summers of
> 2025 and 2026 against a typical pair of summers. Population grew 2,895,000
> against a typical 1,063,000. The labor force grew 3,953,000 against a typical
> 3,802,000. Employment grew 4,284,000 against a typical 4,867,000 — 583,000
> slower than normal.

**chart_waterfall.png**

> Waterfall chart showing how the U.S. labor force went from a typical two
> summers of growth, 6,156,000, to actual growth of 2,455,000 across the summers
> of 2025 and 2026. Foreign-born men account for 1,796,000 of the 3,701,000
> shortfall, or 49 percent; foreign-born women 1,606,000, or 43 percent;
> native-born women 449,000, or 12 percent. Native-born men added 151,000 more
> than a typical two summers, partly offsetting the shortfall.

**table_flows.png**

> Table of foreign-born and native-born men by labor force status, showing the
> January-to-July change for 2025, for 2026, the combined total, and a typical
> two summers. The foreign-born male population fell 1,170,000 then 919,000, a
> combined 2,089,000, against a typical 40,000.

**table_sources.png**

> Table listing the BLS Current Population Survey series identifiers used in this
> analysis for population, labor force, employment, unemployment, not in labor
> force, participation rate, and employment-population ratio, for foreign-born and
> native-born men.

---

## Open Graph / social

```html
<meta property="og:type"        content="article">
<meta property="og:title"       content="The Men Who Vanished: 2.1 Million Gone From the Jobs Data">
<meta property="og:description" content="The foreign-born male population has fallen 2.1 million across two summers — the two steepest on record. 88% came straight out of employment, not the sidelines.">
<meta property="og:image"       content="REPLACE_ME_PRISMIC_HERO_URL?auto=format,compress">
<meta property="og:image:alt"   content="The foreign-born male population of the United States, 2007 to July 2026, with the January-to-July declines of 2025 and 2026 highlighted.">
<meta property="og:url"         content="https://www.data4thepeople.com/p/the-men-who-vanished">
<meta property="og:site_name"   content="Data 4 The People">
<meta property="article:published_time" content="2026-08-29T06:00:00-04:00">
<meta property="article:section" content="Data 4 Thought">
<meta property="article:author"  content="Eric Pachman">

<meta name="twitter:card"        content="summary_large_image">
<meta name="twitter:title"       content="The Men Who Vanished: 2.1 Million Gone From the Jobs Data">
<meta name="twitter:description" content="They did not stop looking for work. Eighty-eight percent came straight out of jobs.">
<meta name="twitter:image"       content="REPLACE_ME_PRISMIC_HERO_URL?auto=format,compress">

<meta name="keywords" content="foreign born labor force, foreign born population, immigration labor market, Bureau of Labor Statistics, BLS, Current Population Survey, CPS, labor force participation, native born workers, employment population ratio, labor supply, jobs report, economic data">
```

---

## Schema (JSON-LD)

Follows the standard Data 4 Thought post format.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "The Men Who Vanished: 2.1 Million Gone From the Jobs Data",
  "description": "The foreign-born male population has fallen 2.1 million across two summers — the two steepest January-to-July declines on record. Eighty-eight percent came straight out of employment, and native-born men did not fill the gap.",
  "image": [
    "REPLACE_ME_PRISMIC_HERO_URL?auto=format,compress"
  ],
  "datePublished": "2026-08-29T06:00:00-04:00",
  "dateModified": "2026-08-29T06:00:00-04:00",
  "author": {
    "@type": "Person",
    "name": "Eric Pachman",
    "url": "https://www.data4thepeople.com/authors/eric-pachman"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Data 4 The People",
    "url": "https://data4thepeople.com"
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://www.data4thepeople.com/p/the-men-who-vanished"
  },
  "keywords": [
    "foreign born labor force",
    "immigration labor market",
    "Current Population Survey",
    "employment population ratio",
    "labor supply"
  ],
  "articleSection": "Data 4 Thought",
  "inLanguage": "en-US",
  "citation": [
    {
      "@type": "CreativeWork",
      "name": "Civilian noninstitutional population, foreign born, men, not seasonally adjusted, series LNU00073396",
      "author": "U.S. Bureau of Labor Statistics",
      "url": "https://data.bls.gov/timeseries/LNU00073396"
    },
    {
      "@type": "CreativeWork",
      "name": "Employment level, foreign born, men, not seasonally adjusted, series LNU02073396",
      "author": "U.S. Bureau of Labor Statistics",
      "url": "https://data.bls.gov/timeseries/LNU02073396"
    },
    {
      "@type": "CreativeWork",
      "name": "Employment-population ratio, native born, men, not seasonally adjusted, series LNU02373414",
      "author": "U.S. Bureau of Labor Statistics",
      "url": "https://data.bls.gov/timeseries/LNU02373414"
    },
    {
      "@type": "CreativeWork",
      "name": "The Employment Situation — July 2026",
      "author": "U.S. Bureau of Labor Statistics",
      "url": "https://www.bls.gov/news.release/empsit.nr0.htm"
    },
    {
      "@type": "CreativeWork",
      "name": "Current Population Survey, LN database",
      "author": "U.S. Bureau of Labor Statistics",
      "url": "https://www.bls.gov/cps/"
    }
  ]
}
</script>
```

**Notes**

- `image` carries the hero only, matching the house format. Prismic's delivery
  URL already ends in `?auto=format,compress` — keep that on.
- Hero filename, following the convention:
  `2026-08-29-the-men-who-vanished-hero-1680x1080.png`
- `datePublished` uses the usual 06:00 ET. This post is not pegged to a release
  morning, so it does not need the 10:00 treatment the July participation post
  used.
- Five citations rather than three: the nativity story rests on three specific
  series that a reader should be able to pull up individually, plus the release
  and the survey.

---

## A note on framing

This post touches immigration, and it will be read by people who want it to say
something it does not say. Two guardrails are load-bearing and should survive
editing:

1. **The CPS cannot distinguish emigration from non-response.** The post says
   this explicitly in "What this does not tell you." Do not let a headline or
   pull quote upgrade "stopped being counted" to "left the country" or
   "deported." The data does not support either word.
2. **The two summers are added, never measured end to end.** The 2.1 million is
   the sum of two January-to-July windows, each inside one calendar year. The
   change between July 2025 and January 2026 is deliberately not counted,
   because it spans a population-control seam. Do not "simplify" this into a
   single March-2025-to-July-2026 span; that figure is 2.2 million and it
   crosses the seam.
3. **Every comparison is against the same window in other years.** The
   "typical two summers" column is not decoration — the series are unadjusted
   and January-to-July is seasonal, so a raw change means nothing without it.

If an editor wants a shorter version, cut the labor-force-share section before
cutting any of those three.

---

## Reusing this next month

The headline figures are specific to the July 2026 data. Anything below has to
be re-derived, not copied:

- the 2.1 million combined decline and its 1,170,000 / 919,000 split
- the 88 / 12 / 0 shares of the gap against a typical two summers
- "the two steepest January-to-July declines on record"
- the 49% share of the labor-force shortfall and the 10.2% share of the labor force
- the four-way waterfall split (49 / 43 / 12 / −4) and the 92% foreign-born total
- the 583,000 native-born employment shortfall
- `datePublished` / `dateModified`

Note that the reference period for "a typical two summers" (2013-2024 excluding
2020) will need revisiting as more years accumulate.

`python analysis/foreign-born-men/make_charts.py` prints the current values and
regenerates every image.
