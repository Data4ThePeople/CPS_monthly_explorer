# Publishing metadata — "The Men Who Vanished"

Everything Prismic needs for this post. Drafted 2026-08-29.

Replace the `REPLACE_ME` value before publishing: the Prismic image delivery URL
for the hero. Confirm the `/p/` slug matches what Prismic assigns.

---

## Email

**Subject:** The government's own data contradicts the government's story

**Preview text** (79 chars — first 39 survive mobile truncation):

> Not the idle. The employed. Eighty-eight percent came straight out of jobs.

Do not lead the preview with "foreign-born." The finding is the mechanism —
people leaving the count from *employment* rather than drifting into
not-in-the-labor-force — and a nativity label in the first 39 characters gets the
post sorted into a political bucket before the mechanism is read. "Not the idle.
The employed." does the work without naming the group, and it is the sentence the
whole piece turns on.

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

> If the people leaving were a drag on the economy, the decline would show up in unemployment or the sidelines. It doesn't. 88% came straight out of jobs.

Alternative (152 chars), leading with the labor force framing:

> Foreign-born men are 10% of the labor force and roughly half of its shortfall on two independent measures. Foreign-born women are rising. It is the men, specifically.

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

> Line chart of the employment-population ratio for native-born men, July of each
> year from 2015 to 2026. The ratio falls from 65.9 percent in July 2019 to 60.1
> percent in July 2020, recovers to 64.2 percent by 2023, then declines in each of
> the last three years, from 64.2 percent in 2023 to 62.8 percent in July 2026. A hollow marker at 63.6 percent
> marks where the ratio would need to sit for native-born men to have absorbed
> the 971,000 jobs foreign-born men vacated — 0.8 points above the actual figure.

**chart_divergence.png**

> Line chart of the civilian labor force for foreign-born men and foreign-born
> women, 2008 to July 2026, on a trailing twelve-month average. Both rise
> together until 2025. The men's line peaks in June 2025 and falls to 17,954,000
> by July 2026, while the women's line continues rising to 14,497,000.

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
  "description": "The foreign-born male population has fallen 2.1 million across two summers. If those leaving were a drag on the economy, the decline would appear in unemployment or the sidelines; instead 88% came straight out of employment, on the government's own published data.",
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
4. **Do not extend any claim to foreign-born women, or to a four-way split.**
   The methodology section explains why: the two-window method manufactures a
   decline for women that three other measures contradict, and the January 2026
   controls moved about 1.5 million between men and women. Foreign-born men are
   the only group that revision barely touched. If an editor wants "immigrants
   are leaving," the honest version is "foreign-born men are," and the
   divergence chart is the evidence.

If an editor wants a shorter version, cut the labor-force-share section before
cutting any of those three.

**On the standard-deviation figures.** Do not convert them into a probability,
a "one in n years event," or a percentage chance, however tempting the headline.
With seventeen reference observations the tail of the distribution is not
characterised, and normality would be carrying the claim rather than the data.
The post says this explicitly and the sentence must survive editing. "Nothing in
the recorded history of this series looks like this" is the strongest form the
claim can honestly take.

Related: the paragraph asking readers not to let the 2.1 million stand on its
own is not false modesty. The level is a model estimate. Its significance comes
from the longitudinal record and from native-born men sitting at +0.1 sigma over
the identical months. An edit that promotes the 2.1 million to the whole story
strips out exactly what makes it defensible.

**On "What if nobody was supposed to replace them?"** This is the only section
of the post that goes beyond what the data shows, and it says so twice in its
own text. The occupation table is measured and can be defended line by line. The
consequence — that the work goes undone and prices rise — is a hypothesis, and
the paragraph beginning "We want to be explicit that we have not measured this"
is what keeps the section honest. It is not padding and it is not hedging. Cut
it and the piece is making an economic forecast it has not earned. The promise
to publish the test "whether or not it agrees with what we have just written" is
also load-bearing; do not soften it.

**On the framing added in "The story we are being told makes a prediction."**
That section argues the data refutes a claim about *who* left — the idle versus
the employed — and that claim genuinely is refuted, on the government's own
series. It does not argue, and must not be edited to argue, that the data shows
deportation, emigration, or any particular mechanism. The CPS cannot see the
difference and the post says so twice. Keep the sentence in the closing that
concedes it: "We cannot tell you from this data why any individual person
stopped being counted." Losing that line turns a defensible argument into an
indefensible one.

---

## Reusing this next month

The headline figures are specific to the July 2026 data. Anything below has to
be re-derived, not copied:

- the 2.1 million combined decline and its 1,170,000 / 919,000 split
- the 88 / 12 / 0 shares of the gap against a typical two summers
- "the two steepest January-to-July declines on record"
- the 49% share of the labor-force shortfall and the 10.2% share of the labor force
- the 47% cross-check on a July-to-July basis
- the twelve-month-average divergence (men −691,000, women +371,000)
- the 583,000 native-born employment shortfall
- `datePublished` / `dateModified`

Note that the reference period for "a typical two summers" (2013-2024 excluding
2020) will need revisiting as more years accumulate.

`python analysis/foreign-born-men/make_charts.py` prints the current values and
regenerates every image.
