# Labor force flows — copy for two pages

The explorer carries the CPS labor force flows (BLS lfst codes 70–84, 90 series,
monthly from February 1990) and neither page mentions them. The schema now
advertises them, so the copy should too.

Figures below are **July 2026, seasonally adjusted**. They change with every
release. Refresh with:

```
python v2/flows_copy.py
```

| Flow | July 2026 |
|---|---:|
| Employed → not in labor force | 4,994,000 |
| Employed → unemployed | 1,261,000 |
| Not in labor force → employed | 4,600,000 |
| Unemployed → employed | 1,676,000 |

---

## A. Visualization page — `beyond-the-unemployment-rate`

Short and factual. Goes in the section describing what the tool contains.

> **Labor force flows.** The explorer also carries the monthly flows — how many
> people moved between employed, unemployed and not in the labor force from one
> month to the next, published monthly since 1990. These are the only official
> figures that show someone going straight from a job to outside the labor force
> without ever being counted as unemployed. In July 2026 that was **5.0 million
> people**, against 1.3 million who became unemployed.

---

## B. Intro post — `cps-intro-post`

Longer, because here the flows are evidence for the argument the piece already
makes: that the unemployment rate cannot see millions of people. Place it after
the passage establishing that claim, before the call to go use the tool.

> ### The clearest way to see what the rate misses
>
> Every month, BLS publishes something almost nobody looks at: the labor force
> flows. Not how many people are working, but how many *moved* — between having
> a job, looking for one, and being outside the labor force altogether.
>
> In July, 1.3 million people went from employed to unemployed. That is the flow
> the unemployment rate is built to see. It is the number that becomes a
> headline.
>
> In the same month, **5.0 million people went from employed to not in the labor
> force** — straight from a job to outside the count, without ever being recorded
> as unemployed. Four times as many.
>
> Most of that is ordinary. People retire. People go back to school. People stop
> working to look after someone. The point is not that five million people were
> secretly laid off. The point is that the unemployment rate cannot tell you
> which is which, because it never saw any of them.
>
> And it works the same way in reverse. Of the people who started a job in July,
> 1.7 million came from unemployment. **4.6 million came from outside the labor
> force entirely.** Most people who got a job last month were not, by the
> official definition, looking for one.
>
> That is the gap. Not an error in the unemployment rate — it measures exactly
> what it was designed to measure — but a limit on what one number can carry.
> The flows have been published monthly since 1990. They are free. Almost nobody
> charts them.
>
> So we did.

---

## Notes

- The ratio has widened. Employed-to-sidelines ran 1.8× employed-to-unemployed
  in 1995; it is 3.3× so far in 2026. Worth a sentence if either page wants one.
- These are seasonally adjusted series (LNS17*). The explorer also carries the
  unadjusted set (LNU07*).
- Flows begin February 1990, not 1948 like the level series. Do not let either
  page imply the flows run the full eighty years.
