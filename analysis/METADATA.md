# Publishing metadata — "The Line the BLS Buried"

Everything Prismic needs for this post. Published 2026-08-07.

Replace the three `REPLACE_ME` values before publishing: the article URL, the
image base URL Prismic serves from, and the site root.

---

## Email

**Subject:** The terrifying line the BLS buried

**Preview text** (78 chars — first 39 survive mobile truncation):

> Only one year since 1948 has been worse. We paid people to stay home that year.

Do not put "0.7 percentage point" alone in the preview. Out of context it reads
as trivially small, which is the exact misreading the post exists to correct.

---

## Title

**Use this** (58 chars — fits Google's ~60 char display):

> The Line the BLS Buried: Participation Hits a 1975 Low

Alternatives:

| Angle | Title | Chars |
|---|---|---:|
| Search-first | Labor Force Participation Falls to Lowest July Since 1975 | 61 |
| Finding-first | It Isn't Retirement: Who Is Actually Leaving the Labor Force | 59 |

The email subject and the SEO title should differ. The subject sells the open;
the title has to survive a search results page.

---

## Meta description

**Use this** (154 chars):

> The BLS buried it six paragraphs in: participation has fallen 0.7 points since January — the steepest January-to-July drop in 79 years outside the pandemic.

Alternative (157 chars), leading with the counterintuitive finding:

> Participation just hit its lowest July since 1975. We expected retiring boomers. Aging explains 6% of it — prime-age workers explain nearly half.

---

## Meta keywords

```
labor force participation rate, labor force participation, Bureau of Labor
Statistics, BLS, Current Population Survey, CPS, prime-age workers, prime age
labor force, jobs report, labor market, workforce participation, population
aging, shift-share analysis, July 2026 jobs report, economic data
```

**Worth knowing:** Google has ignored the `<meta name="keywords">` tag since
2009 and it carries no ranking weight. It is included because Prismic exposes
the field and because some internal site searches, syndication partners, and
non-Google engines still read it. Filling it in is harmless; expecting SEO
benefit from it is not. The `keywords` property inside the JSON-LD below is the
one that does modern work.

---

## Alt text

**hero_participation.png**

> Line chart of the U.S. labor force participation rate from 1948 to July 2026.
> The rate rises from about 59% in the 1950s to a 67.3% peak in 2000, declines
> for two decades, plunges during COVID-19 in 2020, partially recovers, then
> falls to 61.4% in July 2026 — the lowest July reading since 1975.

**chart_ranking.png**

> Bar chart of the ten steepest January-to-July declines in the U.S. labor force
> participation rate since 1948. 2020 is largest at negative 1.8 percentage
> points, 2026 is second at negative 0.7, followed by 1952 and 1953 at negative
> 0.6.

**table_levels.png**

> Table of U.S. population and labor force by age group, January to July 2026.
> Total population rose 606,000 while the labor force fell 1,371,000. The 25 to
> 54 population grew 179,000 but its labor force fell 628,000.

**table_decomposition.png**

> Table decomposing the 0.7 percentage point fall in the labor force
> participation rate. Participation among 25 to 54 year-olds accounts for 48
> percent of the decline, ages 55 and over 26 percent, ages 16 to 24 20 percent,
> and population aging only 6 percent.

**table_sources.png**

> Table listing the BLS Current Population Survey series identifiers used in this
> analysis for participation rate, labor force level, and civilian
> noninstitutional population, by age group.

If you use a screenshot from the live explorer, write its alt text to match the
view you actually captured — alt text has to describe the real image.

---

## Open Graph / social

Prismic usually keeps these separate from JSON-LD. Set them explicitly, or
platforms may grab whichever image they find first.

```html
<meta property="og:type"        content="article">
<meta property="og:title"       content="The Line the BLS Buried: Participation Hits a 1975 Low">
<meta property="og:description" content="The BLS buried it six paragraphs in: participation has fallen 0.7 points since January — the steepest January-to-July drop in 79 years outside the pandemic.">
<meta property="og:image"       content="REPLACE_ME_PRISMIC_HERO_URL?auto=format,compress">
<meta property="og:image:alt"   content="U.S. labor force participation rate, 1948 to July 2026, falling to 61.4% — the lowest July reading since 1975.">
<meta property="og:url"         content="https://www.data4thepeople.com/p/the-line-the-bls-buried">
<meta property="og:site_name"   content="Data 4 The People">
<meta property="article:published_time" content="2026-08-07T10:00:00-04:00">
<meta property="article:section" content="Data 4 Thought">
<meta property="article:author"  content="Eric Pachman">

<meta name="twitter:card"        content="summary_large_image">
<meta name="twitter:title"       content="The Line the BLS Buried: Participation Hits a 1975 Low">
<meta name="twitter:description" content="Only one year since 1948 has been worse. We paid people to stay home that year.">
<meta name="twitter:image"       content="REPLACE_ME_PRISMIC_HERO_URL?auto=format,compress">

<meta name="keywords" content="labor force participation rate, labor force participation, Bureau of Labor Statistics, BLS, Current Population Survey, CPS, prime-age workers, jobs report, labor market, workforce participation, population aging, shift-share analysis, economic data">
```

---

## Schema (JSON-LD)

Follows the standard Data 4 Thought post format.

Fill in before publishing: the Prismic image URL (upload the hero first, then
paste its delivery URL), and the `/p/` slug if it differs from the one below.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "The Line the BLS Buried: Participation Hits a 1975 Low",
  "description": "The BLS buried it six paragraphs in: participation has fallen 0.7 points since January — the steepest January-to-July drop in 79 years outside the pandemic. Aging explains only 6% of it.",
  "image": [
    "REPLACE_ME_PRISMIC_HERO_URL?auto=format,compress"
  ],
  "datePublished": "2026-08-07T10:00:00-04:00",
  "dateModified": "2026-08-07T10:00:00-04:00",
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
    "@id": "https://www.data4thepeople.com/p/the-line-the-bls-buried"
  },
  "keywords": [
    "labor force participation rate",
    "prime-age workers",
    "Current Population Survey",
    "labor market",
    "jobs report"
  ],
  "articleSection": "Data 4 Thought",
  "inLanguage": "en-US",
  "citation": [
    {
      "@type": "CreativeWork",
      "name": "Labor force participation rate, 16 years and over, seasonally adjusted, series LNS11300000",
      "author": "U.S. Bureau of Labor Statistics",
      "url": "https://data.bls.gov/timeseries/LNS11300000"
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
- Suggested hero filename, following the convention:
  `2026-08-07-the-line-the-bls-buried-hero-1680x1080.png`
- `datePublished` is set to 10:00 ET rather than the usual 06:00, since the BLS
  release lands at 08:30 ET and a timestamp before it would be wrong. Adjust to
  the actual publish time.
- The three citations point at the exact series, the release being critiqued,
  and the survey — the same granularity as citing CAINC4 and CUUR0000SA0 rather
  than just "BEA" and "BLS".

---

## Reusing this next month

The headline figures are specific to the July 2026 release. Anything below has
to be re-derived, not copied:

- the 0.7-point change and the 61.4% level
- "lowest July since 1975"
- the 48% / 6% decomposition split
- `datePublished` / `dateModified`

`python analysis/make_charts.py` prints the current values and regenerates every
image.
