# Publishing metadata — "The Men Who Vanished"

Everything Prismic needs for this post. Drafted 2026-08-30.

The hero has been uploaded, so the image URLs below are live rather than
placeholders. Confirm the `/p/` slug matches what Prismic assigns.

Companion files: `POST.md` (the piece), `EMAIL.md` (the Mailchimp teaser).

---

## Email

**Subject:** The missing men were working

**Preview text** (93 chars):

> Not the idle. The employed. We tested it against nineteen years of the government's own data.

Do not lead the preview with "foreign-born," and do not lead with Springfield.
A nativity label in the first 39 characters gets the post sorted into a
political bucket before the mechanism is read; a place name reads as local
news. "Were working" carries the whole surprise.

---

## Title

**Use this** (58 chars — fits Google's ~60 char display):

> The Men Who Vanished: Testing Labor Market Displacement

Alternates:

| Angle | Title | Chars |
|---|---|---:|
| Finding-first | The Missing Men Were Working, Not Idle | 38 |
| Search-first | Do Immigrants Take American Jobs? What the Data Shows | 53 |
| Place-first | What Springfield Ohio Reveals About the Labor Force | 51 |

The email subject and the SEO title should differ. The subject sells the open;
the title has to survive a search results page.

---

## Meta description

**Use this** (156 chars):

> If the people leaving were a drag on the economy, the decline would show up in unemployment or the sidelines. It doesn't. 88% came straight out of jobs.

Alternative (152 chars), leading with the second test:

> Foreign-born men are 10% of the labor force and roughly half its shortfall. Native-born men's employment rate has fallen three years running, not risen.

---

## Meta keywords

```
foreign born labor force, foreign born population, immigration labor market,
Bureau of Labor Statistics, Current Population Survey, labor force
participation, native born workers, employment population ratio, labor supply,
labor market displacement, task specialization, Springfield Ohio, Temporary
Protected Status, Clark County Ohio, jobs report
```

Google has ignored `<meta name="keywords">` since 2009. It is filled in because
Prismic exposes the field; the `keywords` property in the JSON-LD is the one
that does modern work.

---

## Alt text

Each of these is already in `POST.md` — the importer reads them from the
Markdown, so they only need editing there. Reproduced here for review.

**hero_foreign_born_men.png**

> The foreign-born male population of the United States, 2007 to July 2026,
> falling from about 25 million in early 2025 to 22.8 million, with the
> January-to-July windows of 2025 and 2026 highlighted.

**chart_ranking.png**

> Change in the foreign-born male population from January to July, every year
> from 2007 to 2026. 2025 is steepest at negative 1,170,000 and 2026 second at
> negative 919,000; the third steepest is 2020 at negative 336,000.

**chart_where_they_went.png**

> Change in foreign-born men by labor force status across the summers of 2025
> and 2026, against a typical pair of summers. Employment normally rises 835,000
> but instead fell 971,000, while unemployment and not-in-labor-force behaved
> close to normal.

**table_gap.png**

> Of the gap against a typical two summers, employment accounts for negative
> 1,806,000 or 88 percent, not in labor force negative 252,000 or 12 percent,
> and unemployment positive 11,000 or zero percent.

**chart_not_filled.png**

> Employment-population ratio for native-born men, July of each year from 2015
> to 2026, declining in each of the last three years to 62.8 percent, against a
> hollow marker at 63.6 percent showing where it would need to sit to absorb the
> vacated jobs.

**table_occupations.png**

> Foreign-born men as a share of all men employed in each occupation in 2025:
> 42 percent in farming, fishing and forestry, 34 percent in construction, 30
> percent in building and grounds maintenance, down to 18 percent in management
> and professional work and 10 percent in protective service.

**chart_divergence.png**

> Civilian labor force for foreign-born men and foreign-born women, 2008 to July
> 2026, on a trailing twelve-month average. The men's line peaks in mid-2025 and
> falls while the women's continues rising.

**table_sources.png**

> Table listing the BLS Current Population Survey series identifiers used for
> population, labor force, employment, unemployment, not in labor force,
> participation rate and employment-population ratio, for foreign-born and
> native-born men.

---

## Cover images

Both are set in the post's front matter and filled by the importer.

| Field | Tab | File |
|---|---|---|
| `featured_image` | Main | `2026-08-29-the-men-who-vanished-hero-1680x1080.png` |
| `meta_image` | SEO & Metadata | the same file |

The 1680×1080 is drawn at that size with its type scaled for a narrow canvas.
The 2400px `hero_foreign_born_men.png` is the first figure in the body and is
too wide to serve as a link preview.

---

## Open Graph / social

```html
<meta property="og:type"        content="article">
<meta property="og:title"       content="The Men Who Vanished: Testing Labor Market Displacement">
<meta property="og:description" content="If the people leaving were a drag on the economy, the decline would show up in unemployment or the sidelines. It doesn't. 88% came straight out of jobs.">
<meta property="og:image"       content="https://images.prismic.io/data4thepeople/pRDE4e92vRAVgXTq_2026-08-29-the-men-who-vanished-hero-1680x1080.png?auto=format,compress">
<meta property="og:image:alt"   content="The foreign-born male population of the United States, 2007 to July 2026, with the January-to-July declines of 2025 and 2026 highlighted.">
<meta property="og:url"         content="https://www.data4thepeople.com/p/the-men-who-vanished">
<meta property="og:site_name"   content="Data 4 The People">
<meta property="article:published_time" content="2026-08-30T06:00:00-04:00">
<meta property="article:section" content="Data 4 Thought">
<meta property="article:author"  content="Eric Pachman">

<meta name="twitter:card"        content="summary_large_image">
<meta name="twitter:title"       content="The Men Who Vanished: Testing Labor Market Displacement">
<meta name="twitter:description" content="Not the idle. The employed. Eighty-eight percent came straight out of jobs.">
<meta name="twitter:image"       content="https://images.prismic.io/data4thepeople/pRDE4e92vRAVgXTq_2026-08-29-the-men-who-vanished-hero-1680x1080.png?auto=format,compress">
```

---

## Schema (JSON-LD)

The importer generates this from the front matter and writes it to the `schema`
field. Reproduced here so it can be reviewed without opening Prismic.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "The Men Who Vanished: Testing Labor Market Displacement",
  "description": "If the people leaving were a drag on the economy, the decline would show up in unemployment or the sidelines. It doesn't. 88% came straight out of jobs.",
  "image": "https://images.prismic.io/data4thepeople/pRDE4e92vRAVgXTq_2026-08-29-the-men-who-vanished-hero-1680x1080.png?auto=format,compress",
  "datePublished": "2026-08-30T06:00:00-04:00",
  "dateModified": "2026-08-30T06:00:00-04:00",
  "articleSection": "Data 4 Thought",
  "inLanguage": "en-US",
  "isAccessibleForFree": true,
  "keywords": [
    "foreign born labor force",
    "labor market displacement",
    "task specialization",
    "Current Population Survey",
    "Springfield Ohio"
  ],
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
  }
}
```

---

## Framing guardrails

These are the places where an edit could quietly turn a defensible piece into
an indefensible one.

**1. Do not reintroduce the phrase "replacement theory."** The post tests
*labor market displacement* — the ordinary economic claim that immigrants take
jobs that would otherwise go to non-immigrants. The Great Replacement is Renaud
Camus's white nationalist conspiracy theory about elites deliberately replacing
white populations. Moreno made a jobs claim; filing it under replacement theory
attributes a conspiracy theory to a sitting senator, and that becomes the story
instead of the data.

**2. The CPS cannot distinguish emigration from non-response.** The post says so
twice. Do not let a headline or pull quote upgrade "stopped being counted" to
"deported" or "left the country." The data does not support either word.

**3. Do not let the 2.1 million stand on its own.** Its force comes from being
unprecedented against the series' own record *and* from native-born men sitting
at +0.1 sigma over the identical months. Alone it is a level estimate from a
model.

**4. Do not convert the standard deviations into a probability.** No "one in n
years." Seventeen reference observations cannot characterise a tail; normality
would be carrying the claim rather than the data.

**5. Do not extend any claim to foreign-born women, or to a four-way split.**
The methodology explains why. Foreign-born women's labor force is *rising*.

**6. Springfield is the frame, not the proof.** One metro, small preliminary
numbers. The national series carries the argument. In particular, do not claim
Haitian arrivals rescued Springfield manufacturing — the post explicitly refuses
that claim, because employment there collapsed a decade before they arrived.

**7. Keep the International Motors paragraph.** 1,341 jobs end in Springfield
in October on a corporate sale. If the local numbers fall this autumn, a reader
needs that before attributing it to TPS. Naming it first is much stronger than
having it pointed out.

If an editor wants a shorter version, cut the Springfield history before cutting
any of the above.

---

## Reusing this next month

The headline figures are specific to the July 2026 data. Anything below has to
be re-derived, not copied:

- the 2.1 million decline and its 1,170,000 / 919,000 split
- the 88 / 12 / 0 shares of the gap against a typical two summers
- "the two steepest January-to-July declines on record"
- the 49% share of the labor-force shortfall, and its 45–48% stability check
- the 62.8% native-born employment rate and the 63.6% counterfactual
- the −5.7 and −4.6 sigma figures
- the occupation shares, which are annual and update each spring
- `datePublished` / `dateModified`

`python analysis/foreign-born-men/make_charts.py` prints every national number
in the post and regenerates all eight images. The Springfield figures come from
the Census API and FRED and are not in that script; their tables and series IDs
are named in the post's methodology.
