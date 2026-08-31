# Teaser email — Mailchimp

A full research piece, so this follows the Day 7 pattern rather than the
Days 1–6 one. The post runs about 3,700 words — roughly 2,200 of argument and
1,500 of limits and methodology — and carries two falsification tests. None of
that belongs in an inbox. This email carries one finding, one chart, and the
caveat that keeps the finding honest.

The thread to pull is the mechanism, not the headline number. "2.1 million are
gone" starts an argument about immigration. "The ones who left were the ones
working" starts a question, and the question is the piece.

Springfield stays out of the subject line and out of the first block. It is the
frame of the post, but in an inbox a place name reads as local news and the list
is national.

Companion file: `analysis/foreign-born-men/METADATA.md` (page meta, JSON-LD,
alt text, framing guardrails).

Fill one placeholder before sending: `[[POST URL]]`.

---

## Subject line

```
Two million foreign-born men have vanished
```

42 characters. It names the scale and the group up front and lets the preheader
carry the twist. Longer than the mobile cut, so the words that have to survive
truncation are "Two million foreign-born men" — which is the story.

Alternates if you want to A/B:

```
The missing men were working
```
```
Nobody took the jobs back
```

The first withholds the group entirely and leads on the mechanism, which travels
further with readers who have not been following the story. The second is the
plainest statement of the second half of the piece.

## Preview text (preheader)

```
Most of the missing men were not unemployed or not in the labor force. They were working.
```

88 characters. It does not repeat the subject: the subject states the scale, the
preheader states the finding. Naming both of the not-working boxes is the point
— it is what makes "they were working" land as a result rather than an
assertion. Set it in Mailchimp's preview-text field, **not** as the first line
of body copy.

---

## Layout, block by block

Mailchimp default 600px content width.

### 1 — Kicker

```
Beyond the Unemployment Rate · Labor force
```

### 2 — Why this one is short

```
This one is long — two claims tested, a trip to Springfield, and the limits of what the data can carry. Here is the finding; the rest is on the page.
```

### 3 — Headline

```
The men who vanished
```

### 4 — Deck

```
2.1 million foreign-born men have gone from the count across two summers. Almost all of them were working, and native-born men have not taken the jobs.
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

It does not. Unemployment fell by 464,000, against a typical 475,000 for two summers — normal to within eleven thousand people. The not-in-the-labor-force count moved a little more than usual, and carries twelve percent of it.

Employment fell by 971,000, against a normal increase of 835,000. Eighty-eight percent of the missing men came straight out of jobs.

We are also told these were our jobs, taken. That is checkable too, and the last two years handed it the cleanest test it will ever get: roughly a million jobs were vacated. If they had been taken from native-born men, they are now sitting there to be taken back.

Native-born men's employment rate has fallen in each of the last three Julys, to 62.8%. Absorbing those jobs would have required 63.6%.
```

### 8 — The native-born chart

| | |
|---|---|
| file | `analysis/foreign-born-men/chart_not_filled.png` |
| size | 2080×1280, 161 KB |

Alt text:

```
Line chart of the employment-population ratio for native-born men, July of each year from 2015 to 2026. It rises to 65.9 percent in 2019, falls to 60.1 percent in 2020, recovers to 64.2 percent by 2023, then declines in each of the last three years to 62.8 percent. A hollow marker at 63.6 percent shows where it would need to sit for native-born men to have absorbed the 971,000 jobs foreign-born men vacated — 0.8 points above the actual figure.
```

Then this **as live text underneath**, because the annotations on the chart will
not be legible at phone width:

```
Native-born men's employment rate, every July. To absorb the vacated jobs it needed to reach 63.6%. It is 62.8%, and has fallen three years running.
```

This chart earns its place because it is the picture of the paragraph directly
above it — the body copy ends on 62.8% against 63.6%, and this is that gap drawn.
Like the hero it survives a 600px column by being a shape: a recovery, a slide,
and a marked gap at the end. The numbers on it are unreadable at that size, which
is what the line underneath is for.

### 9 — How big is it

**Live text.** The sizing is four numbers and a stability check; no chart
carries that better than a sentence.

```
Foreign-born men are one worker in ten. But over the past two years, they are roughly half of the entire shortfall in the American labor force — about four and a half times their weight.

We recomputed that share against six different definitions of normal growth. It came back 45, 45, 45, 45, 47 and 48 percent.

We are playing with fire.
```

### 10 — Button

```
Read the full analysis
```

Point it at `[[POST URL]]`.

### 11 — What is on the page and not in this email

```
On the page: why foreign-born women's labor force is rising while the men's falls — which is how we know this is not simply an undercount, what Springfield, Ohio looked like before the Haitians arrived and what happened to its factories, the economics of why immigrants and native-born workers are not interchangeable, which occupations these men actually held, why these two summers are the steepest on record and how we measured them without crossing a population-control seam, what a four-and-a-half-sigma departure does and does not entitle you to say, and the analysis we tried and threw away.
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
Source: U.S. Bureau of Labor Statistics, Current Population Survey (LN database), series LNU00073396, LNU01073396, LNU02073396, LNU03073396, LNU05073396 and their native-born counterparts. Not seasonally adjusted; BLS publishes no seasonally adjusted series by nativity. Springfield figures from the Census Bureau's American Community Survey and BLS series SPRI239MFG.

Every figure, the script that builds it, and the verification:
github.com/Data4ThePeople/CPS_monthly_explorer
```

---

## Notes

- **Only two of the eight images belong in an email.** The 1680×1080 hero and
  the native-born chart are shapes and survive a 600px column. The rest do not:
  `chart_ranking.png` is 1900px wide with forty labels at 10pt — on a 375px
  phone that renders near 2px. The four tables are worse, being type all the way
  down. Their findings run as live text in blocks 6 and 9 instead.
- **Images off is the failure mode to design against.** With images suppressed
  this email must still say: what happened, what the two claims predicted, that
  both failed, how big it is, and what we cannot claim. That is why blocks 2, 6,
  7, 9 and 12 are all live text.
- **Springfield is deliberately held back to block 11.** It is the post's
  opening and its emotional frame, but it is also the part a national list will
  read as someone else's local news. The email leads with the finding and uses
  Springfield as a reason to click through.
- **One number in block 9 will move.** "Roughly half" is 47–49% on current data
  and stable at 45–48% across six baselines, but it is recomputed from the
  latest release. Re-run `make_charts.py` on send morning if the August data has
  landed; it prints every national figure in this email.
- **Do not let an editor promote the 2.1 million to the whole story.** Its force
  comes from being unprecedented against the series' own record *and* from
  native-born men sitting at +0.1 sigma over the identical months. This is
  guardrail 3 in METADATA.md and it applies to the email more than the page.
- **Total image payload is about 288 KB** — the hero at 127 KB plus the
  native-born chart at 161 KB. If you want it lighter, compress the second one;
  it is a single line on a flat ground and tolerates JPEG at quality 80.
- **The parchment ground is `#faf3df`.** Both images are drawn on it edge to
  edge, so either set the Mailchimp content background to match or give them
  padding — on white they will read as unintentional cream rectangles.
