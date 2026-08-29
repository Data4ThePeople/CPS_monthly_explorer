# Teaser email — Mailchimp

A full research piece, so this send follows the Day 7 pattern rather than the
Days 1–6 one. The post runs about 2,900 words, carries two falsification tests,
a five-method sizing exercise and a methodology section that exists to survive
hostile reading. None of that belongs in an inbox. This email carries one
finding, one chart, and the caveat that keeps the finding honest.

The thread to pull is the mechanism, not the headline number. "2.1 million are
gone" invites an argument about immigration. "The ones who left were the ones
working" invites a question, and the question is the piece.

Companion file: `analysis/foreign-born-men/METADATA.md` (page meta, JSON-LD,
alt text, framing guardrails).

Fill one placeholder before sending: `[[POST URL]]`.

---

## Subject line

```
The missing men were working
```

28 characters, well inside the mobile cut. Deliberately no number and no
nativity label — the finding sorts people into camps the instant it names a
group, and a subject line has no room for the mechanism that makes it
interesting. "Were working" carries the whole surprise: whatever you assumed
about who left, it was not that.

Alternates if you want to A/B:

```
Nobody took the jobs back
```
```
Two million left. They were not the idle ones.
```

The first is the plainest statement of the second half of the piece and reads
well to anyone following the labor data. The second is the strongest and the
most likely to be forwarded as a political claim rather than a measurement — if
you use it, the preheader has to carry "the government's own data."

## Preview text (preheader)

```
Not the idle. The employed. We tested it against nineteen years of the government's own data.
```

93 characters. It does not repeat the subject: the subject states the finding,
the preheader says what we did to earn it. "The government's own data" is doing
real work — it pre-empts the first objection, which is that this is advocacy
arithmetic. Set it in Mailchimp's preview-text field, **not** as the first line
of body copy.

---

## Layout, block by block

Mailchimp default 600px content width.

### 1 — Kicker

```
Beyond the Unemployment Rate · Labor force
```

### 2 — Why this one is short

One line, under the headline. This piece is long and the list should know the
email is a door, not a summary.

```
This one is long — two claims tested, a sizing exercise, and the limits of what the data can carry. Here is the finding; the rest is on the page.
```

### 3 — Headline

```
The men who vanished
```

### 4 — Deck

```
2.1 million foreign-born men have gone from the count across two summers. We tested the two stories being told about why — and both fail against the government's own numbers.
```

### 5 — Hero image, linked

| | |
|---|---|
| file | `analysis/foreign-born-men/2026-08-29-the-men-who-vanished-hero-1680x1080.png` |
| size | 1680×1080, 127 KB |
| link | `[[POST URL]]` |

Alt text:

```
Line chart of the foreign-born male population of the United States from 2007 to July 2026, rising from 17.3 million to about 25 million by early 2025, then falling to 22.8 million. Two segments are marked: January to July 2025, down 1.2 million, and January to July 2026, down 0.9 million.
```

Purpose-built at this size with its type scaled for the narrower canvas, so it
is the one hero in the set that survives a 600px column. Do not substitute
`hero_foreign_born_men.png`; it is drawn at 2400px for the page.

### 6 — Key figures

Set these as **live text**, not `chart_where_they_went.png`. Roughly a third of
recipients read with images off, and these three lines are the email. Keep the
comparison on each one — the raw numbers mean nothing without the "normally"
beside them.

```
−971,000 — the fall in foreign-born men's employment across two summers, against a normal rise of 835,000
−464,000 — the fall in their unemployment, against a normal fall of 475,000. An ordinary summer.
88% — the share of the shortfall that came out of jobs rather than the sidelines
```

### 7 — Body copy

Five short paragraphs. This is the whole argument; the page carries the proof.

```
We are told the people leaving were a drag on the economy. That is checkable, because it makes a prediction. Every person aged 16 and over is employed, unemployed, or not in the labor force. There is no fourth box. If the men who disappeared were not working, the decline has to show up in the last two.

It does not. Unemployment fell by 464,000, against a typical 475,000 — a normal summer to within eleven thousand people. The not-in-the-labor-force count moved a little more than usual, and carries twelve percent of it.

Employment fell by 971,000, against a normal increase of 835,000. Eighty-eight percent of the missing men came straight out of jobs.

We are also told these were our jobs, taken. That is checkable too, and the last two years handed it the cleanest test it will ever get: roughly a million jobs were vacated. If they had been taken from native-born men, they are now sitting there to be taken back.

Native-born men's employment rate has fallen in each of the last three Julys, to 62.8%. Absorbing those jobs would have required 63.6%.
```

### 8 — The divergence chart

| | |
|---|---|
| file | `analysis/foreign-born-men/chart_divergence.png` |
| size | 2200×1280, 151 KB |

Alt text:

```
Line chart of the civilian labor force for foreign-born men and foreign-born women, 2008 to July 2026, on a trailing twelve-month average. Both rise together until 2025, when the men's line peaks and turns down to 17,954,000 while the women's continues rising to 14,497,000.
```

Then this **as live text underneath**, because the chart's legend will not be
legible at phone width:

```
Foreign-born men, falling. Foreign-born women, still rising. Over the year to July 2026: men down 691,000, women up 371,000.
```

This is the one chart in the set that belongs in an email. It is a shape — two
lines separating — and the shape survives the downscale even when the type does
not. It also does real defensive work: a general "immigrants are leaving" story
would pull both lines down. Only one moves.

### 9 — How big is it

**Live text.** The sizing is four numbers and a stability check; no chart
carries that better than a sentence.

```
Foreign-born men are one worker in ten. They are roughly half of the entire shortfall in the American labor force — about four and a half times their weight.

We recomputed that share against six different definitions of normal growth. It came back 45, 45, 45, 45, 47 and 48 percent.
```

### 10 — Button

```
Read the full analysis
```

Point it at `[[POST URL]]`.

### 11 — What is on the page and not in this email

```
On the page: why these two summers are the steepest on record and how we measured them without crossing a population-control seam, what happened to foreign-born women and why it is not what the first cut of the data suggested, which occupations these men actually held, what a four-and-a-half-sigma departure does and does not entitle you to say, and the analysis we tried and threw away.
```

### 12 — The caveat

**Do not cut this.** It is the difference between analysis and alarmism, and an
email is exactly where "stopped being counted" gets forwarded as "deported."

```
What this does not tell you

The Current Population Survey counts people who live at a sampled address and answer the door. When someone stops being counted, it cannot tell you whether they left the country, moved somewhere the sample did not reach, or stopped opening the door to a federal interviewer. We cannot settle that, and we do not try.

These are also model-based figures, and the model has error — that is what the January revisions are. So do not read 2.1 million as precise to the person.

What is not in doubt is who left. Not the idle. The employed.
```

### 13 — Footer

```
Source: U.S. Bureau of Labor Statistics, Current Population Survey (LN database), series LNU00073396, LNU01073396, LNU02073396, LNU03073396, LNU05073396 and their native-born counterparts. Not seasonally adjusted; BLS publishes no seasonally adjusted series by nativity.

Every figure, the script that builds it, and the verification:
github.com/Data4ThePeople/CPS_monthly_explorer
```

---

## Notes

- **Only two of the seven images belong in an email.** The 1680×1080 hero and
  the divergence chart are shapes and survive a 600px column. The rest do not:
  `chart_ranking.png` is 1900px wide with twenty year-labels and twenty value
  labels at 10pt — on a 375px phone that renders near 2px. `table_flows.png` and
  `table_sources.png` are worse, being type all the way down. Their findings are
  carried as live text in blocks 6 and 9 instead.
- **Images off is the failure mode to design against.** With images suppressed
  this email must still say: what happened, what the two stories predicted, that
  both failed, how big it is, and what we cannot claim. That is why blocks 2, 6,
  7, 9 and 12 are all live text.
- **The subject line is doing more work than usual.** Every phrasing that names
  the group up front tested badly against the guardrail in METADATA.md: a
  nativity label in the first 39 characters gets the post sorted into a
  political bucket before the mechanism is read. "The missing men were working"
  is the finding with the sorting removed.
- **One number in block 9 will move.** "Roughly half" is 47–49% on current data
  and stable at 45–48% across six baselines, but it is recomputed from the
  latest release. Re-run `make_charts.py` on send morning if the August data has
  landed; it prints every figure in this email.
- **Do not let an editor promote the 2.1 million to the whole story.** Its force
  comes from being unprecedented against the series' own record *and* from
  native-born men sitting at +0.1 sigma over the identical months. Alone it is a
  level estimate from a model. This is the fourth guardrail in METADATA.md and
  it applies to the email more than the page.
- **Total image payload is about 278 KB** — the hero at 127 KB plus the
  divergence chart at 151 KB. If you want it lighter, the divergence chart is
  the one to compress; it is two flat lines on a flat ground and tolerates JPEG
  at quality 80 without visible loss.
- **The parchment ground is `#faf3df`.** Both images are drawn on it edge to
  edge, so either set the Mailchimp content background to match or give them
  padding — on white they will read as unintentional cream rectangles.
