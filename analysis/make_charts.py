#!/usr/bin/env python3
"""Charts for the Jan-Jul 2026 labor force participation analysis.

Every value is computed from the cached BLS series at render time -- nothing is
hardcoded -- so re-running after a data revision produces corrected charts
rather than silently stale ones.

Palette note: the brand's teal (#0a3d33) and coral (#712B13) separate by only
dE 4.8 under protanopia, below the dE>=6 floor, so they must never encode
meaning against each other. The base bar uses a desaturated slate-green
(#5d6b64) instead: dE 17.4 normal, 16.5 worst-case CVD, 5.1:1 on parchment.

    python analysis/make_charts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2"))
import bls_client

OUT = Path(__file__).resolve().parent

PARCH   = "#faf3df"   # chart surface
BASE    = "#5d6b64"   # ordinary bars
HILITE  = "#712B13"   # the bar the story is about
INK     = "#2b2317"
MUTED   = "#6b5d3f"
GRID    = "#cdbb96"
SERIF   = ["Georgia", "Times New Roman", "DejaVu Serif"]

LFPR_16 = "LNS11300000"
AGES = {"16-24": ("LNS11324887", "LNU00024887"),
        "25-54": ("LNS11300060", "LNU00000060"),
        "55+":   ("LNS11324230", "LNU00024230")}
JAN, JUL = pd.Timestamp(2026, 1, 1), pd.Timestamp(2026, 7, 1)


def style(ax, title, subtitle, xlabel):
    ax.set_facecolor(PARCH)
    ax.figure.patch.set_facecolor(PARCH)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=10, length=0)
    ax.xaxis.grid(True, color=GRID, lw=0.8, alpha=0.55)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=10, labelpad=10)
    ax.set_title(title, color="#0a3d33", fontsize=16, fontweight="bold",
                 family=SERIF, loc="left", pad=26)
    ax.text(0, 1.035, subtitle, transform=ax.transAxes, color=MUTED,
            fontsize=10.5, style="italic", family=SERIF, va="bottom")


def source(fig, lines, fs=1.0):
    """Footnote block. Takes a list of short lines -- a single long string
    silently runs off the canvas rather than wrapping. `fs` scales type for
    narrower canvases, where a line that fits at 12in will overflow."""
    for i, line in enumerate(reversed(lines)):
        fig.text(0.012, 0.010 + i * (0.028 / fs), line, color=MUTED,
                 fontsize=8.5 * fs, family=SERIF)


def series(sid):
    return bls_client.fetch([sid]).set_index("date")["value"].sort_index()


# --------------------------------------------------------------------------
# table -> PNG (Prismic cannot embed a markdown table)

def render_table(path, title, subtitle, colgroups, headers, rows, aligns,
                 widths, footnotes, hi_rows=(), rule_before=(), figsize=None):
    """Draw a table as an image. `rows` is a list of cell-string lists;
    `hi_rows` are row indices drawn in the highlight colour and bold."""
    nrow = len(rows)
    fig_h = (figsize[1] if figsize else
             1.55 + 0.34 * nrow + 0.22 * len(footnotes) + (0.3 if colgroups else 0))
    fig_w = figsize[0] if figsize else 11.0
    fig = plt.figure(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(PARCH)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    L, R = 0.028, 0.985
    total_w = sum(widths)
    edges, x = [], L
    for w in widths:
        edges.append(x); x += (R - L) * w / total_w
    edges.append(R)

    def cell_x(i, align):
        if align == "l": return edges[i] + 0.004
        if align == "r": return edges[i + 1] - 0.010
        return (edges[i] + edges[i + 1]) / 2

    y = 1 - (0.30 / fig_h)
    fig.text(L, y, title, color="#0a3d33", fontsize=15.5, fontweight="bold",
             family=SERIF, va="top")
    y -= 0.29 / fig_h
    if subtitle:
        fig.text(L, y, subtitle, color=MUTED, fontsize=10.5, style="italic",
                 family=SERIF, va="top")
        y -= 0.30 / fig_h

    if colgroups:
        for label, i0, i1 in colgroups:
            xc = (edges[i0] + edges[i1 + 1]) / 2
            fig.text(xc, y, label, color=MUTED, fontsize=9.5, family=SERIF,
                     ha="center", va="top", fontweight="bold")
            ax.plot([edges[i0] + 0.004, edges[i1 + 1] - 0.006],
                    [y - 0.16 / fig_h] * 2, color=GRID, lw=0.9)
        y -= 0.30 / fig_h

    for i, htxt in enumerate(headers):
        fig.text(cell_x(i, aligns[i]), y, htxt, color=MUTED, fontsize=10,
                 family=SERIF, ha={"l": "left", "r": "right", "c": "center"}[aligns[i]],
                 va="top")
    y -= 0.20 / fig_h
    ax.plot([L, R], [y, y], color="#9a7b2e", lw=1.3)

    rh = 0.34 / fig_h
    for r, row in enumerate(rows):
        y -= rh
        if r in rule_before:
            ax.plot([L, R], [y + rh * 0.86, y + rh * 0.86], color=GRID, lw=0.9)
        hi = r in hi_rows
        for i, cell in enumerate(row):
            fig.text(cell_x(i, aligns[i]), y + rh * 0.30, cell,
                     color=HILITE if hi else INK,
                     fontsize=11.5, family=SERIF,
                     fontweight="bold" if hi else "normal",
                     ha={"l": "left", "r": "right", "c": "center"}[aligns[i]],
                     va="center")
    y -= 0.16 / fig_h
    ax.plot([L, R], [y, y], color="#9a7b2e", lw=1.3)

    for fn in footnotes:
        y -= 0.24 / fig_h
        fig.text(L, y, fn, color=MUTED, fontsize=9, family=SERIF, va="top")

    fig.savefig(path, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {path}")


# --------------------------------------------------------------------------
def chart_hero(path=None, figsize=(12, 6.3), fs=1.0):
    """Hero: the whole 1948-2026 sweep of the headline participation rate.

    Reindexed to a complete monthly range so the uncollected Oct-2025 month
    becomes NaN and matplotlib breaks the line there instead of drawing a
    straight segment across a month that was never measured.

    `fs` scales type so the same design holds at more than one canvas size --
    matplotlib sizes fonts in absolute points, so a smaller figure with
    unchanged sizes comes out looking crowded.
    """
    s = series(LFPR_16)
    full = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    s = s.reindex(full)
    gaps = int(s.isna().sum())

    peak_at = s.idxmax(); peak = s.max()
    last_at = s.dropna().index[-1]; last = s.dropna().iloc[-1]
    jan26 = s[JAN]

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor(PARCH); fig.patch.set_facecolor(PARCH)

    ax.plot(s.index, s.values, color=BASE, lw=2.0, zorder=3)
    # The window the story is about, drawn over the top.
    win = s.loc[JAN:last_at]
    ax.plot(win.index, win.values, color=HILITE, lw=3.2, zorder=4,
            solid_capstyle="round")
    ax.plot([last_at], [last], "o", color=HILITE, ms=9, zorder=5,
            markeredgecolor=PARCH, markeredgewidth=2)
    ax.plot([peak_at], [peak], "o", color=BASE, ms=7, zorder=5,
            markeredgecolor=PARCH, markeredgewidth=2)

    ax.annotate(f"Peak {peak_at.year}\n{peak:.1f}%",
                xy=(peak_at, peak), xytext=(peak_at - pd.DateOffset(years=13), peak + 0.9),
                fontsize=11*fs, family=SERIF, color=MUTED, ha="center",
                arrowprops=dict(arrowstyle="-", color=GRID, lw=1))
    # Label sits beside its own dot -- a long leader from the left would cross
    # the 2020 plunge and read as though it pointed there.
    ax.text(last_at + pd.DateOffset(months=8), last - 0.15,
            f"July 2026\n{last:.1f}%", fontsize=12.5*fs, family=SERIF,
            color=HILITE, fontweight="bold", ha="left", va="center")
    # No January-2026 callout: any leader long enough to reach clear space
    # rakes across the 2010s and reads as pointing at the wrong thing. The
    # coral segment already marks the window; the exact endpoints are in the
    # post. jan26 is kept for the stdout summary below.
    ax.annotate("COVID-19", xy=(pd.Timestamp(2020, 4, 1), 60.05),
                xytext=(pd.Timestamp(2011, 6, 1), 59.1),
                fontsize=10*fs, family=SERIF, color=MUTED, style="italic",
                ha="center",
                arrowprops=dict(arrowstyle="-", color=GRID, lw=1))

    ax.set_ylim(58, 68.5)
    ax.set_xlim(s.index.min() - pd.DateOffset(years=1),
                s.index.max() + pd.DateOffset(years=9))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=11*fs, length=0)
    ax.yaxis.grid(True, color=GRID, lw=0.8, alpha=0.5)
    ax.set_axisbelow(True)

    fig.text(0.055, 0.955, "U.S. LABOR FORCE PARTICIPATION RATE",
             color="#9a7b2e", fontsize=11*fs, family=SERIF, fontweight="bold",
             va="top")
    fig.text(0.055, 0.905, "The lowest July reading since 1975",
             color="#0a3d33", fontsize=21*fs, family=SERIF, fontweight="bold",
             va="top")
    source(fig, ["BLS Current Population Survey, series LNS11300000 (seasonally "
                 "adjusted), January 1948 - July 2026.",
                 "The break in the line is October 2025, which was never "
                 "collected. · Data 4 The People"], fs=fs)
    fig.tight_layout(rect=(0.012, 0.045 + (0.03 if fs < 1 else 0.022), 1, 0.86))
    p = Path(path) if path else OUT / "hero_participation.png"
    fig.savefig(p, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {p}  (peak {peak:.1f} in {peak_at:%Y-%m}, "
          f"last {last:.1f} in {last_at:%Y-%m} (Jan {jan26:.1f}), {gaps} missing month(s))")


# --------------------------------------------------------------------------
def chart_ranking():
    """Top 10 steepest Jan->Jul declines in the 16+ participation rate."""
    s = series(LFPR_16)
    rows = []
    for y in range(s.index.year.min(), s.index.year.max() + 1):
        a, b = pd.Timestamp(y, 1, 1), pd.Timestamp(y, 7, 1)
        if a in s.index and b in s.index:
            rows.append((y, round(s[b] - s[a], 1)))
    t = pd.DataFrame(rows, columns=["year", "chg"]).nsmallest(10, "chg")
    t = t.sort_values("chg")                       # steepest at top after invert
    n_years = len(rows)

    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ypos = range(len(t))
    colors = [HILITE if y == 2026 else BASE for y in t.year]
    ax.barh(list(ypos), t.chg, color=colors, height=0.68, zorder=3)
    ax.set_yticks(list(ypos))
    ax.set_yticklabels([str(int(y)) for y in t.year],
                       fontsize=11, family=SERIF,
                       color=INK)
    for lbl, y in zip(ax.get_yticklabels(), t.year):
        if y == 2026:
            lbl.set_fontweight("bold"); lbl.set_color(HILITE)
    ax.invert_yaxis()

    for i, (y, c) in enumerate(zip(t.year, t.chg)):
        ax.text(c - 0.035, i, f"{c:+.1f}", va="center", ha="right",
                fontsize=10.5, family=SERIF, color=INK,
                fontweight="bold" if y == 2026 else "normal")

    ax.annotate("COVID-19 shutdown", xy=(-1.79, 0.34), xytext=(-1.72, 1.15),
                fontsize=9.5, family=SERIF, color=MUTED, style="italic",
                arrowprops=dict(arrowstyle="-", color=GRID, lw=1))
    # Anchored well clear of the -0.7 value label, which sits at x~-0.74.
    ax.annotate("2026 — steepest on record\noutside the pandemic",
                xy=(-0.72, 1.34), xytext=(-1.86, 4.4), ha="left",
                fontsize=10.5, family=SERIF, color=HILITE, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=HILITE, lw=1.2,
                                connectionstyle="angle3,angleA=0,angleB=70"))

    ax.set_xlim(-2.0, 0.02)
    style(ax,
          "Only one January-to-July has ever fallen further",
          f"Change in the labor force participation rate, January to July, "
          f"10 steepest declines of {n_years} years",
          "Percentage-point change, January to July")
    source(fig, ["BLS Current Population Survey, series LNS11300000 "
                 "(seasonally adjusted), 1948-2026 · Data 4 The People"])
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    p = OUT / "chart_ranking.png"
    fig.savefig(p, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {p}")
    return t


# --------------------------------------------------------------------------
def tables():
    """Emit the decomposition as markdown tables (deliberately not a chart --
    the levels carry the argument better than bars do). Printing them from the
    data keeps POST.md correctable after a BLS revision."""
    lfpr = {g: series(sa) for g, (sa, _) in AGES.items()}
    pop  = {g: series(ps) for g, (_, ps) in AGES.items()}
    head = series(LFPR_16)
    clf  = {g: series(c) for g, c in
            {"16-24": "LNS11024887", "25-54": "LNS11000060",
             "55+": "LNS11024230"}.items()}
    clf["16+"] = series("LNS11000000")
    pop["16+"] = series("LNU00000000")

    tot_j = sum(pop[g][JAN] for g in AGES)
    tot_l = sum(pop[g][JUL] for g in AGES)
    parts = []
    for g in AGES:
        w0 = pop[g][JAN] / tot_j
        d  = lfpr[g][JUL] - lfpr[g][JAN]
        parts.append((g, w0 * d, w0, d))
    compo = sum(lfpr[g][JAN] * (pop[g][JUL]/tot_l - pop[g][JAN]/tot_j)
                for g in AGES)
    published = head[JUL] - head[JAN]

    within = sum(v for _, v, _, _ in parts)
    total  = within + compo

    print("\n### Absolute levels, January to July 2026 (thousands)\n")
    print("| Age group | Population Jan | Population Jul | Change | "
          "Labor force Jan | Labor force Jul | Change |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for g in list(AGES) + ["16+"]:
        dp = pop[g][JUL] - pop[g][JAN]
        dc = clf[g][JUL] - clf[g][JAN]
        name = "**16+ (total)**" if g == "16+" else g
        print(f"| {name} | {pop[g][JAN]:,.0f} | {pop[g][JUL]:,.0f} | "
              f"{dp:+,.0f} | {clf[g][JAN]:,.0f} | {clf[g][JUL]:,.0f} | "
              f"{dc:+,.0f} |")

    print("\n### What produced the decline\n")
    print("| Source | Share of 16+ population | Participation-rate change | "
          "Contribution | Share of decline |")
    print("|---|---:|---:|---:|---:|")
    for g, v, w, d in sorted(parts, key=lambda x: x[1]):
        name = f"**{g} participation**" if g == "25-54" else f"{g} participation"
        print(f"| {name} | {100*w:.1f}% | {d:+.1f} pp | {v:+.2f} pp | "
              f"{100*v/total:.0f}% |")
    print(f"| Population aging (age mix) | — | — | {compo:+.2f} pp | "
          f"{100*compo/total:.0f}% |")
    print(f"| **Total explained** | | | **{total:+.2f} pp** | |")
    print(f"| Published change | | | {published:+.1f} pp | |")
    print(f"\n_Components sum to {total:+.2f} pp against a published "
          f"{published:+.1f} pp; the gap is rounding._")

    # ---- the same two tables as PNGs, for Prismic ----
    n = lambda v: f"{v:,.0f}"
    sgn = lambda v: f"{v:+,.0f}"

    rows = []
    for g in list(AGES) + ["16+"]:
        label = "16+ (total)" if g == "16+" else g
        rows.append([label,
                     n(pop[g][JAN]), n(pop[g][JUL]), sgn(pop[g][JUL]-pop[g][JAN]),
                     n(clf[g][JAN]), n(clf[g][JUL]), sgn(clf[g][JUL]-clf[g][JAN])])
    render_table(
        OUT / "table_levels.png",
        "The population grew. The labor force shrank.",
        "Civilian noninstitutional population and labor force, January to July 2026, thousands",
        [("POPULATION", 1, 3), ("LABOR FORCE", 4, 6)],
        ["Age group", "January", "July", "Change", "January", "July", "Change"],
        rows,
        ["l", "r", "r", "r", "r", "r", "r"],
        [1.5, 1.0, 1.0, 0.95, 1.0, 1.0, 0.95],
        ["Population not seasonally adjusted; labor force seasonally adjusted. BLS adjusts each series",
         "independently, so the age groups do not sum exactly to the published 16+ total.",
         "BLS Current Population Survey · Data 4 The People"],
        hi_rows=(3,), rule_before=(3,))

    drows = []
    for g, v, w, d in sorted(parts, key=lambda x: x[1]):
        drows.append([f"{g} participation", f"{100*w:.1f}%", f"{d:+.1f} pp",
                      f"{v:+.2f} pp", f"{100*v/total:.0f}%"])
    drows.append(["Population aging (age mix)", "—", "—",
                  f"{compo:+.2f} pp", f"{100*compo/total:.0f}%"])
    drows.append(["Total explained", "", "", f"{total:+.2f} pp", ""])
    drows.append(["Published change", "", "", f"{published:+.1f} pp", ""])
    render_table(
        OUT / "table_decomposition.png",
        "Aging explains 6% of it. Prime-age workers explain 48%.",
        "What produced the January-July 2026 fall in the 16+ participation rate",
        None,
        ["Source", "Share of 16+ pop.", "Rate change", "Contribution", "Share of decline"],
        drows,
        ["l", "r", "r", "r", "r"],
        [2.0, 1.15, 0.95, 1.0, 1.1],
        [f"Components sum to {total:+.2f} pp against the published {published:+.1f} pp; "
         "the gap is rounding, as BLS publishes rates to one decimal.",
         "Participation rates seasonally adjusted, population not seasonally adjusted "
         "· Data 4 The People"],
        hi_rows=(0,), rule_before=(4,))

    render_table(
        OUT / "table_sources.png",
        "Every figure, and the exact BLS series it came from",
        "Current Population Survey (LN database). Look any of these up at bls.gov.",
        None,
        ["Measure", "16-24", "25-54", "55+", "16+ total"],
        [["Participation rate (seasonally adj.)",
          "LNS11324887", "LNS11300060", "LNS11324230", "LNS11300000"],
         ["Labor force level (seasonally adj.)",
          "LNS11024887", "LNS11000060", "LNS11024230", "LNS11000000"],
         ["Civilian noninst. population (NSA)",
          "LNU00024887", "LNU00000060", "LNU00024230", "LNU00000000"]],
        ["l", "c", "c", "c", "c"],
        [1.9, 1.0, 1.0, 1.0, 1.0],
        ["BLS publishes no seasonally adjusted population series -- population controls carry no",
         "seasonal component by construction. · Data 4 The People"])


if __name__ == "__main__":
    chart_hero()
    chart_hero(OUT / "2026-08-07-the-line-the-bls-buried-hero-1680x1080.png",
               figsize=(8.4, 5.4), fs=0.78)
    chart_ranking()
    tables()
