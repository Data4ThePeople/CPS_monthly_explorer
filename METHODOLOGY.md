# CPS Monthly Explorer — Methodology

## Where the data comes from

Every number in this tool comes straight from the U.S. Bureau of Labor Statistics' Current Population Survey, the monthly household survey of about 60,000 homes that the government has run since 1940. The series shown here begin in January 1948 and run through June 2026.

We now pull the monthly values directly from the BLS Public Data API, the agency's own official service, at `api.bls.gov/publicAPI/v2`. We do not use any third-party feed, and we do not touch the numbers after we read them.

## How the pieces fit together

The survey's published output is not one file but a catalog of tens of thousands of separate series, and this tool is really just a careful way of stitching them back together. Anyone can rebuild what we built.

The backbone is the **series catalog**, `ln.series`, published as a flat file at `download.bls.gov/pub/time.series/ln`. Each of its 68,630 rows is one published series: a unique series ID, a title, the first and last dates it covers, and a column for each characteristic — age, sex, race, nativity, industry, occupation, and about thirty others. Those characteristic columns hold short codes rather than words. A companion set of small **mapping files**, one per characteristic, translates the codes into plain English: `ln.ages` turns code 65 into "65 years and over," `ln.sexs` turns 1 into "Men," `ln.lfst` turns 40 into "Unemployment rate."

The catalog tells us *which* series exist and what each one measures. The API supplies the **monthly values**. We still read the catalog from the flat file for a specific reason: the API has no catalog endpoint. It will return the history of any series ID you name, but it cannot tell you what series exist or what combination of characteristics a given ID represents. Only `ln.series` can. So the catalog comes from the flat file, and every observation comes from the API.

Building the tool is four steps:

1. We read `ln.series` and every mapping file, and join the codes to their labels, so each series carries a human-readable description on every characteristic.
2. For each characteristic we identify its standard total — the code that means "everyone" — by matching the label text ("Both Sexes," "All Races," "16 years and over").
3. We work out which combinations are actually published: for a given characteristic and value, we keep the one series where that characteristic is set and every other characteristic sits at its total. That is what guarantees one clean series per view. Of the 68,630 series in the catalog, 2,151 qualify, spanning 21 characteristics and 188 groups.
4. We request exactly those 2,151 series from the API and hand the results to the chart.

The full build costs about 176 API requests against a daily allowance of 500. Responses are stored locally, so rebuilding the tool afterward costs nothing and returns identical results.

One important detail from the BLS documentation shapes all of this: **series ID codes cannot be decoded by eye.** BLS states plainly that only the first three letters are meaningful — `LNS` for seasonally adjusted, `LNU` for not seasonally adjusted — and that everything after that must be looked up rather than parsed. So the tool never guesses a series ID. It reads the catalog, matches on the characteristic columns, and uses whatever ID BLS assigned.

## The one rule: one published series per view

Every chart you see is a single, official BLS series. Nothing is summed. Nothing is averaged across series. Nothing is estimated or modeled. When you pick a dimension, a group, and a measure, the tool finds the exact BLS series that matches that combination and shows it to you as published. The series number sits right under each chart, so you can take it to bls.gov and check the figures yourself.

Some combinations are published in more than one form — seasonally adjusted and not, or a current series alongside an older discontinued one. That happened 550 times in this build. When it does, the tool picks one on a fixed rule: it prefers the series that is still being published, then the seasonally adjusted version, then the one with the longest history. It never blends them.

## How we hold everything else steady

The survey has more than thirty ways to slice the data, and most combinations are not published. So when you look at one cut, we hold every other characteristic at its standard total. Choose foreign-born, and the tool shows you foreign-born of all races, all origins, both sexes, sixteen and over, unless you narrow it further. A few characteristics carry their own standard age range, because that is how BLS publishes them: veterans start at eighteen, and educational attainment starts at twenty-five. The subtitle above each chart always spells out exactly what is being held constant, so you are never guessing.

## Seasonal adjustment and the trend line

Many of these series are not seasonally adjusted, which means they carry the regular ups and downs of the calendar — hiring in summer, layoffs after the holidays. For those, the chart draws the raw monthly figure as a thin line and a bold twelve-month moving average on top of it. The bold line is the trend; the thin line is what actually happened each month. When a series is already seasonally adjusted, we show it as a single clean line.

## Two breaks in the record you should know about

**October 2025 was never collected.** Because of the lapse in federal funding, the household survey did not run that month, and BLS published no figure for it. The tool does not estimate or interpolate it. The monthly line breaks at that point rather than drawing straight through, and the twelve-month average goes blank for any window that would have to span the missing month — about 2,400 monthly observations across the tool are affected. A gap in the line means the data is absent, not that the value was zero.

**January 2026 carries a population-control revision.** Each January, BLS resets the population totals the survey is weighted to. The January 2026 reset was unusually large. Levels before and after that month sit on different population bases, so a change measured straight across the seam mixes real movement with the revision. **The explorer plots the published series as-is and does not adjust for this.** When you compare a level before January 2026 to one after it, read the difference with that in mind. Rates and shares are far less affected than headcounts.

## What we checked, and what we did not

We audited this tool against the full catalog of 68,630 series. We confirmed that it selects the correct single series for the combinations it offers, that it always prefers current data over discontinued data, and that where a total and its parts are both published, the parts add up to the total within normal rounding. Where they do not, the cause is in the source data, not the tool: the government rounds each series independently, revised its industry categories in 2002, and defines a few series such as farm employment on a slightly different basis than their parts.

We also checked the move to the API directly against the old method. We rebuilt the entire tool from the API and compared it against the version built from the bulk flat files — all 1,033,903 overlapping monthly observations, across all 2,151 series. Every value matched. The two builds are byte-for-byte identical. The change in how we fetch the data changed nothing about the data.

We did not check every possible cross-comparison, and we cannot rule out every error. That is why we are asking for help. If you find a number that looks wrong, pull the series number from under the chart, compare it against the official BLS table, and tell us what you found. This is public data. It should be checked in the open.

## A note on reading these numbers

A count going up or down is not the same as a rate going up or down. As the country grows and ages, some totals rise simply because there are more people. Where it matters, look at a share or a rate, not just a headcount, and read the trend line rather than any single month. The tool is built to let you do exactly that.

---

*The CPS Monthly Explorer draws entirely on the U.S. Bureau of Labor Statistics' Current Population Survey (LN database). Every view is one published BLS series; no values are combined, averaged, or modeled. Built by Data 4 The People.*
