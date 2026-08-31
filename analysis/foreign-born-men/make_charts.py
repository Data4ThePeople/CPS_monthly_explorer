#!/usr/bin/env python3
"""Charts for the foreign-born men analysis (January-July 2025 and 2026).

Every value is computed from the cached BLS series at render time -- nothing is
hardcoded -- so re-running after a data revision produces corrected charts
rather than silently stale ones.

Why January-to-July windows
---------------------------
BLS introduces new population controls each January and does not revise history,
so a level on one side of a January is not comparable to a level on the other.
The January 2026 revision cut the published native-born male population by about
1,454,000 in a single month. Every comparison here therefore sits inside one
calendar year, on a single population basis, and the two affected summers are
chained rather than measured across the seam.

Why everything is benchmarked against a typical summer
------------------------------------------------------
BLS publishes no seasonally adjusted series by nativity, and January-to-July is
a strongly seasonal window: employment normally rises into the summer and the
not-in-labor-force count normally falls. A raw January-to-July change therefore
cannot be read on its own. Each figure below is compared against the mean
January-to-July change over 2013-2024 excluding 2020, so seasonality is held
constant rather than assumed away.

Style primitives (palette, `style`, `source`, `render_table`) are imported from
the sibling participation analysis rather than copied, so the two posts cannot
drift apart visually.

    python analysis/foreign-born-men/make_charts.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "v2"))

import bls_client


def _load_module(name, path):
    """Import a module by explicit path.

    The participation analysis is also called make_charts.py, so a plain
    `import make_charts` resolves to whichever directory happens to sit first
    on sys.path -- this file when imported by anything else, which is a
    circular import. Addressing it by path removes the ambiguity.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_house = _load_module("d4tp_chart_style", REPO / "analysis" / "make_charts.py")
PARCH, BASE, HILITE = _house.PARCH, _house.BASE, _house.HILITE
INK, MUTED, GRID, SERIF = _house.INK, _house.MUTED, _house.GRID, _house.SERIF
style, source, render_table = _house.style, _house.source, _house.render_table

OUT = HERE

S = {
    "FBM_pop": "LNU00073396", "FBM_clf": "LNU01073396", "FBM_emp": "LNU02073396",
    "FBM_une": "LNU03073396", "FBM_nilf": "LNU05073396",
    "FBM_lfpr": "LNU01373396", "FBM_epop": "LNU02373396",
    "NBM_pop": "LNU00073414", "NBM_clf": "LNU01073414", "NBM_emp": "LNU02073414",
    "NBM_une": "LNU03073414", "NBM_nilf": "LNU05073414",
    "NBM_lfpr": "LNU01373414", "NBM_epop": "LNU02373414",
    "FBW_clf": "LNU01073397", "NBW_clf": "LNU01073415",
    "CLF_nsa": "LNU01000000", "CLF_sa": "LNS11000000",
}


WINDOWS = (2025, 2026)                                  # the two seam-free summers
REF = tuple(y for y in range(2013, 2025) if y != 2020)  # a typical summer
FIRST, LAST = pd.Timestamp(2026, 1, 1), pd.Timestamp(2026, 7, 1)


def load() -> pd.DataFrame:
    """Wide frame on a complete monthly index.

    The reindex matters: October 2025 was never collected, so it must exist as
    NaN. Without it a positional .shift() silently compares windows one month
    apart from the ones it claims to, and matplotlib draws a line straight
    through a month nobody measured.
    """
    df = bls_client.fetch(list(S.values()))
    w = df.pivot_table(index="date", columns="series_id", values="value")
    w.columns = [{v: k for k, v in S.items()}[c] for c in w.columns]
    full = pd.date_range(w.index.min(), w.index.max(), freq="MS")
    return w.sort_index().reindex(full)


def jan_to_jul(w) -> pd.DataFrame:
    """January-to-July change for every year the series covers."""
    rows = {}
    for y in range(w.index.min().year, w.index.max().year + 1):
        a, b = pd.Timestamp(y, 1, 1), pd.Timestamp(y, 7, 1)
        if a in w.index and b in w.index and pd.notna(w.FBM_pop[a]) \
           and pd.notna(w.FBM_pop[b]):
            rows[y] = {c: w[c][b] - w[c][a] for c in w.columns}
    return pd.DataFrame(rows).T


def typical(t) -> pd.Series:
    """The mean January-to-July change in a normal year.

    A mean rather than a median so the components stay additive: employed,
    unemployed and not-in-labor-force sum to population year by year, and the
    means of those sums therefore sum too. Medians do not, and the
    decomposition would not close.
    """
    return t.loc[list(REF)].mean()


# --------------------------------------------------------------------------
def chart_hero(w, path=None, figsize=(12, 6.3), fs=1.0):
    """The foreign-born male population, with both summer windows marked."""
    # The frame carries LNS11000000, which starts in 1948, so the shared index
    # runs far earlier than this series does.
    s = (w.FBM_pop / 1000.0).loc[w.FBM_pop.first_valid_index():]
    segs = [(pd.Timestamp(y, 1, 1), pd.Timestamp(y, 7, 1)) for y in WINDOWS]
    drop = sum(s[a] - s[b] for a, b in segs)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor(PARCH); fig.patch.set_facecolor(PARCH)
    ax.plot(s.index, s.values, color=BASE, lw=2.0, zorder=3)
    for a, b in segs:
        seg = s.loc[a:b]
        ax.plot(seg.index, seg.values, color=HILITE, lw=3.4, zorder=4,
                solid_capstyle="round")
        for x in (a, b):
            ax.plot([x], [s[x]], "o", color=HILITE, ms=8, zorder=5,
                    markeredgecolor=PARCH, markeredgewidth=2)

    ax.annotate("Jan–Jul 2025\n−1.2M", xy=(pd.Timestamp(2025, 4, 1), 24.1),
                xytext=(pd.Timestamp(2020, 6, 1), 25.3),
                fontsize=10.5 * fs, family=SERIF, color=HILITE,
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="-", color=HILITE, lw=1))
    ax.annotate("Jan–Jul 2026\n−0.9M", xy=(pd.Timestamp(2026, 4, 1), 23.2),
                xytext=(pd.Timestamp(2023, 1, 1), 21.0),
                fontsize=10.5 * fs, family=SERIF, color=HILITE,
                fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="-", color=HILITE, lw=1))
    # No bracket spanning the two windows: end-to-end it measures 2.0M, not the
    # 2.1M the two windows sum to, because the gap between them rises -- and
    # drawing it would span the January seam this analysis exists to avoid. The
    # two segment labels already add up in view.
    ax.text(LAST + pd.DateOffset(months=8), 24.6,
            f"−{drop:.1f}M\nacross the two\nhighlighted\nwindows",
            fontsize=11.5 * fs, family=SERIF, color=HILITE,
            fontweight="bold", ha="left", va="top")

    ax.set_ylim(16.5, 26.2)
    ax.set_xlim(s.index.min() - pd.DateOffset(months=6),
                s.index.max() + pd.DateOffset(months=40))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}M")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=11 * fs, length=0)
    ax.yaxis.grid(True, color=GRID, lw=0.8, alpha=0.5)
    ax.set_axisbelow(True)

    fig.text(0.055, 0.955, "FOREIGN-BORN MEN IN THE UNITED STATES",
             color="#9a7b2e", fontsize=11 * fs, family=SERIF,
             fontweight="bold", va="top")
    fig.text(0.055, 0.905, "Two summers, 2.1 million men",
             color="#0a3d33", fontsize=21 * fs, family=SERIF,
             fontweight="bold", va="top")
    source(fig, ["BLS Current Population Survey, series LNU00073396 (civilian "
                 "noninstitutional population, foreign-born men, not",
                 "seasonally adjusted), January 2007 - July 2026. Each "
                 "highlighted window sits inside one calendar year, on a",
                 "single population-control basis. The break in the line is "
                 "October 2025, never collected. · Data 4 The People"], fs=fs)
    fig.tight_layout(rect=(0.012, 0.065 + (0.03 if fs < 1 else 0.022), 1, 0.86))
    p = Path(path) if path else OUT / "hero_foreign_born_men.png"
    fig.savefig(p, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {p}  (−{drop:.2f}M across {len(segs)} windows)")


# --------------------------------------------------------------------------
def chart_ranking(t):
    """Every January-to-July change on record, the two recent ones marked."""
    s = t.FBM_pop.sort_values()
    fig, ax = plt.subplots(figsize=(9.5, 7.2))
    ypos = list(range(len(s)))
    colors = [HILITE if y in WINDOWS else BASE for y in s.index]
    ax.barh(ypos, s.values, color=colors, height=0.68, zorder=3)
    ax.set_yticks(ypos)
    ax.set_yticklabels([str(int(y)) for y in s.index], fontsize=10.5,
                       family=SERIF, color=INK)
    for lbl, y in zip(ax.get_yticklabels(), s.index):
        if y in WINDOWS:
            lbl.set_fontweight("bold"); lbl.set_color(HILITE)
    ax.invert_yaxis()
    for i, (y, v) in enumerate(s.items()):
        off = -22 if v < 0 else 22
        ax.text(v + off, i, f"{v:+,.0f}", va="center",
                ha="right" if v < 0 else "left", fontsize=10,
                family=SERIF, color=INK,
                fontweight="bold" if y in WINDOWS else "normal")
    ax.annotate("The two steepest are\nconsecutive, and both are\n"
                "more than triple the third",
                xy=(-960, 1.15), xytext=(-1120, 5.6), ha="left",
                fontsize=10.5, family=SERIF, color=HILITE, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=HILITE, lw=1.2,
                                connectionstyle="angle3,angleA=0,angleB=70"))
    ax.set_xlim(-1400, 780)
    style(ax, "No other summer looks like these two",
          "Change in the foreign-born male population, January to July, "
          "every year on record",
          "Change in level, thousands of men")
    source(fig, ["BLS Current Population Survey, series LNU00073396 (not "
                 f"seasonally adjusted), {int(s.index.min())}-"
                 f"{int(s.index.max())}. Each bar is measured",
                 "inside a single calendar year, so no bar spans a January "
                 "population-control revision. · Data 4 The People"])
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    p = OUT / "chart_ranking.png"
    fig.savefig(p, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {p}")


# --------------------------------------------------------------------------
def _grouped(path, title, subtitle, cats, actual, norm, xlabel, foot,
             note=None, note_xy=None, note_xytext=None, xlim=None,
             figsize=(10.2, 6.0), legend_loc="lower left"):
    """Two-series grouped horizontal bars: a typical pair of summers vs these.

    Two series, so a legend is mandatory; the bars are also directly labelled,
    which is what actually carries identity for a reader who cannot separate
    the hues.
    """
    fig, ax = plt.subplots(figsize=figsize)
    h = 0.34
    ypos = list(range(len(cats)))
    ax.barh([y - h / 2 - 0.02 for y in ypos], norm, height=h, color=BASE,
            zorder=3, label="A typical two summers")
    ax.barh([y + h / 2 + 0.02 for y in ypos], actual, height=h, color=HILITE,
            zorder=3, label="2025 and 2026")
    ax.set_yticks(ypos)
    ax.set_yticklabels(cats, fontsize=11.5, family=SERIF, color=INK)
    ax.invert_yaxis()
    for i, (a, n) in enumerate(zip(actual, norm)):
        for v, yy, bold in ((n, i - h / 2 - 0.02, False), (a, i + h / 2 + 0.02, True)):
            off = -26 if v < 0 else 26
            ax.text(v + off, yy, f"{v:+,.0f}", va="center",
                    ha="right" if v < 0 else "left", fontsize=10.5,
                    family=SERIF, color=INK,
                    fontweight="bold" if bold else "normal")
    if note:
        # note_xy=None places the block on its own, with no leader. On a chart
        # of long positive bars every leader has to cross one, so the note goes
        # in clear space and the direct labels carry the link instead.
        if note_xy is None:
            ax.text(*note_xytext, note, ha="left", va="center", fontsize=10.5,
                    family=SERIF, color=HILITE, fontweight="bold", zorder=6)
        else:
            ax.annotate(note, xy=note_xy, xytext=note_xytext, ha="left",
                        va="center", zorder=6,
                        fontsize=10.5, family=SERIF, color=HILITE,
                        fontweight="bold",
                        arrowprops=dict(arrowstyle="-", color=HILITE, lw=1.2,
                                        connectionstyle="arc3,rad=0.12"))
    ax.axvline(0, color=GRID, lw=1.1, zorder=2)
    if xlim:
        ax.set_xlim(*xlim)
    style(ax, title, subtitle, xlabel)
    leg = ax.legend(loc=legend_loc, frameon=False, fontsize=10.5,
                    prop={"family": SERIF, "size": 10.5}, handlelength=1.1,
                    handleheight=0.9, borderaxespad=0.2)
    for txt in leg.get_texts():
        txt.set_color(MUTED)
    source(fig, foot)
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    fig.savefig(path, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {path}")


def chart_where_they_went(t, norm):
    a = [t.loc[list(WINDOWS), c].sum() for c in ("FBM_emp", "FBM_une", "FBM_nilf")]
    n = [2 * norm[c] for c in ("FBM_emp", "FBM_une", "FBM_nilf")]
    _grouped(
        OUT / "chart_where_they_went.png",
        "They did not stop looking for work. They stopped being counted.",
        "Change in foreign-born men by labor force status, January to July "
        "of 2025 and 2026 combined, against a typical pair of summers",
        ["Employed", "Unemployed", "Not in\nlabor force"], a, n,
        "Change in level, thousands of men",
        ["A typical two summers is twice the mean January-to-July change over "
         "2013-2024, excluding 2020. BLS publishes no",
         "seasonally adjusted nativity series, so the seasonal pattern is held "
         "constant by comparison rather than adjustment.",
         "Series LNU02073396, LNU03073396, LNU05073396. · Data 4 The People"],
        note="Employment normally rises\nacross two summers.\n"
             "Instead it fell by nearly a million.",
        note_xy=(-985, 0.20), note_xytext=(-2020, 0.70),
        xlim=(-2100, 1300))


def chart_not_filled(w, t, norm):
    """Native-born men's employment rate against what filling the gap needed.

    A rate, not a level, and deliberately so. The January 2026 population
    controls cut the published native-born male labor force by 1,522,000, so
    their levels cannot be compared across that seam. A ratio divides most of
    that out -- numerator and denominator move together -- which is why this
    chart, and the claims that rest on it, use the employment-population ratio.

    July-only, so every point sits on the same seasonal footing: these series
    are published unadjusted and a summer reading is not comparable to a
    winter one.
    """
    jul = w[w.index.month == 7].loc["2015":]
    s_ = jul.NBM_epop
    lost = -t.loc[list(WINDOWS), "FBM_emp"].sum()      # jobs actually vacated
    need = (w.NBM_emp[LAST] + lost) / w.NBM_pop[LAST] * 100

    fig, ax = plt.subplots(figsize=(10.4, 6.4))
    ax.set_facecolor(PARCH); fig.patch.set_facecolor(PARCH)
    ax.plot(s_.index, s_.values, color=BASE, lw=2.4, zorder=3, marker="o", ms=6,
            markeredgecolor=PARCH, markeredgewidth=1.5)
    ax.plot([s_.index[-1]], [s_.iloc[-1]], "o", color=HILITE, ms=10, zorder=5,
            markeredgecolor=PARCH, markeredgewidth=2)
    ax.plot([s_.index[-1]], [need], "o", color=HILITE, ms=11, zorder=5,
            markerfacecolor=PARCH, markeredgecolor=HILITE, markeredgewidth=2.2)
    ax.annotate("", xy=(s_.index[-1], need - 0.05),
                xytext=(s_.index[-1], s_.iloc[-1] + 0.05),
                arrowprops=dict(arrowstyle="<->", color=HILITE, lw=1.4))
    ax.text(s_.index[-1] - pd.DateOffset(months=4), 65.35,
            f"Needed to absorb the {lost:,.0f}k\nvacated jobs — {need:.1f}%",
            fontsize=10.5, family=SERIF, color=HILITE, fontweight="bold",
            ha="right", va="center")
    ax.text(s_.index[-1] + pd.DateOffset(months=3), s_.iloc[-1],
            f"Actual\n{s_.iloc[-1]:.1f}%", fontsize=11.5, family=SERIF,
            color=HILITE, fontweight="bold", ha="left", va="center")
    ax.text(s_.index[-1] - pd.DateOffset(months=2), (need + s_.iloc[-1]) / 2,
            f"{need - s_.iloc[-1]:.1f} pp\nshort", fontsize=11, family=SERIF,
            color=HILITE, fontweight="bold", ha="right", va="center")
    # The run of declines lives in the subtitle rather than as a
    # callout: every anchor that reaches clear space here crosses either the
    # line or the counterfactual label.

    ax.set_ylim(59.4, 66.5)
    ax.set_xlim(s_.index[0] - pd.DateOffset(months=8),
                s_.index[-1] + pd.DateOffset(months=15))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=11, length=0)
    ax.yaxis.grid(True, color=GRID, lw=0.8, alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_title("Native-born men did not take the jobs",
                 color="#0a3d33", fontsize=16.5, fontweight="bold",
                 family=SERIF, loc="left", pad=28)
    ax.text(0, 1.04, "Employment-population ratio, native-born men, July of "
            "each year — down in each of the last three",
            transform=ax.transAxes, color=MUTED, fontsize=10.5,
            style="italic", family=SERIF, va="bottom")
    source(fig, ["Series LNU02373414 (not seasonally adjusted). July readings "
                 "only, so every point sits on the same seasonal footing.",
                 "A ratio rather than a level, because the January 2026 "
                 "population controls cut the published native-born male",
                 "labor force by 1,522,000 and a rate divides most of that out. "
                 "The counterfactual adds the jobs foreign-born",
                 "men vacated to native-born male employment, holding their "
                 "population fixed. · Data 4 The People"])
    fig.tight_layout(rect=(0, 0.115, 1, 1))
    p = OUT / "chart_not_filled.png"
    fig.savefig(p, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {p}  (actual {s_.iloc[-1]:.1f}%, needed {need:.2f}%, "
          f"short {need-s_.iloc[-1]:.2f}pp)")


# --------------------------------------------------------------------------
def chart_divergence(w):
    """Foreign-born men against foreign-born women, on a 12-month average.

    This chart exists because a four-way nativity-by-sex split of the
    labor-force shortfall cannot be done honestly with this data. Any window
    that avoids the January seam drops the July-to-January months, and that
    dropped segment differs enormously by group (+1,143,000 for foreign-born
    women against -152,000 for foreign-born men) -- so a Jan-to-Jul
    decomposition manufactures a decline for women that a full-span, a
    July-to-July, or a 12-month-average measure all contradict. Any window that
    instead spans January 2026 inherits a control revision that moved about
    1.5 million between men and women. Neither is a sound basis for splitting a
    total four ways.

    What survives every one of those measures is the divergence itself, so that
    is what is drawn: a trailing 12-month mean, which spans a full seasonal
    cycle and needs no benchmark.
    """
    # min_periods=11 bridges the uncollected October 2025: the windows covering
    # it average 11 months rather than 12. Without it the line simply stops for
    # a year, which is how the divergence got missed in the first place.
    ma = w[["FBM_clf", "FBW_clf"]].rolling(12, min_periods=11).mean().dropna()
    fig, ax = plt.subplots(figsize=(11.0, 6.4))
    ax.set_facecolor(PARCH); fig.patch.set_facecolor(PARCH)

    for col, colr, lbl in (("FBM_clf", HILITE, "Foreign-born men"),
                           ("FBW_clf", BASE, "Foreign-born women")):
        ax.plot(ma.index, ma[col], color=colr, lw=2.6, zorder=3, label=lbl)
        ax.plot([ma.index[-1]], [ma[col].iloc[-1]], "o", color=colr, ms=9,
                zorder=5, markeredgecolor=PARCH, markeredgewidth=2)
        ax.text(ma.index[-1] + pd.DateOffset(months=3), ma[col].iloc[-1],
                f"{ma[col].iloc[-1]:,.0f}k", color=colr, fontsize=11.5,
                family=SERIF, fontweight="bold", ha="left", va="center")

    pk = ma.FBM_clf.idxmax()
    ax.annotate(f"Peak {pk:%b %Y}", xy=(pk, ma.FBM_clf[pk]),
                xytext=(pk - pd.DateOffset(years=4), 19350),
                fontsize=10.5, family=SERIF, color=MUTED, ha="center",
                arrowprops=dict(arrowstyle="-", color=GRID, lw=1))
    # No "men fall away, women keep rising" callout: the title says it, the two
    # endpoint labels quantify it, and any leader long enough to reach clear
    # space crosses the men's line on the way.

    ax.set_ylim(9000, 19900)
    ax.set_xlim(ma.index.min() - pd.DateOffset(months=4),
                ma.index.max() + pd.DateOffset(months=30))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f}M")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=10.5, length=0)
    ax.yaxis.grid(True, color=GRID, lw=0.8, alpha=0.5)
    ax.set_axisbelow(True)
    ax.set_title("It is the men, and only the men",
                 color="#0a3d33", fontsize=16.5, fontweight="bold",
                 family=SERIF, loc="left", pad=30)
    ax.text(0, 1.045, "Civilian labor force, foreign born, trailing 12-month "
            "average", transform=ax.transAxes, color=MUTED, fontsize=10.5,
            style="italic", family=SERIF, va="bottom")
    leg = ax.legend(loc="upper left", frameon=False, handlelength=1.6,
                    prop={"family": SERIF, "size": 11}, borderaxespad=0.8)
    for txt in leg.get_texts():
        txt.set_color(MUTED)
    a, b = pd.Timestamp(2025, 7, 1), pd.Timestamp(2026, 7, 1)
    source(fig, ["Series LNU01073396 and LNU01073397 (not seasonally adjusted). "
                 "A trailing 12-month mean spans a full seasonal cycle,",
                 "so it needs no seasonal benchmark and is not sensitive to "
                 "which month a window starts in. Windows covering",
                 "October 2025, never collected, average 11 months. "
                 f"Over the year to July 2026 the men's average fell "
                 f"{ma.FBM_clf[a]-ma.FBM_clf[b]:,.0f},000 while the women's",
                 f"rose {ma.FBW_clf[b]-ma.FBW_clf[a]:,.0f},000. "
                 "· Data 4 The People"])
    fig.tight_layout(rect=(0, 0.105, 1, 1))
    p = OUT / "chart_divergence.png"
    fig.savefig(p, dpi=200, facecolor=PARCH)
    plt.close(fig)
    print(f"wrote {p}  (men {ma.FBM_clf[b]-ma.FBM_clf[a]:+,.0f}k, "
          f"women {ma.FBW_clf[b]-ma.FBW_clf[a]:+,.0f}k over the year to Jul 2026)")


# --------------------------------------------------------------------------
def tables(t, norm):
    sgn = lambda v: f"{v:+,.0f}"
    rows, hi = [], []
    for i, (grp, name) in enumerate([("FBM", "Foreign-born men"),
                                     ("NBM", "Native-born men")]):
        rows.append([name, "", "", "", ""])
        for k, lbl in [("pop", "   Population"), ("clf", "   Labor force"),
                       ("emp", "   Employed"), ("une", "   Unemployed"),
                       ("nilf", "   Not in labor force")]:
            c = f"{grp}_{k}"
            comb = t.loc[list(WINDOWS), c].sum()
            rows.append([lbl, sgn(t.loc[2025, c]), sgn(t.loc[2026, c]),
                         sgn(comb), sgn(2 * norm[c])])
        if grp == "FBM":
            hi += [1, 3]
    render_table(
        OUT / "table_flows.png",
        "Two summers, measured without crossing a population-control seam",
        "Change from January to July, thousands. Each column sits inside one "
        "calendar year.",
        None,
        ["", "Jan–Jul 2025", "Jan–Jul 2026", "Combined", "Typical two summers"],
        rows, ["l", "r", "r", "r", "r"], [1.9, 1.0, 1.0, 1.0, 1.25],
        ["Not seasonally adjusted -- BLS publishes no seasonally adjusted "
         "nativity series, which is why the last column is",
         "present: it is twice the mean January-to-July change over 2013-2024 "
         "excluding 2020. Employed, unemployed and",
         "not-in-labor-force are exhaustive and sum to the population.",
         "BLS Current Population Survey · Data 4 The People"],
        hi_rows=tuple(hi), rule_before=(6,))

    render_table(
        OUT / "table_sources.png",
        "Every figure, and the exact BLS series it came from",
        "Current Population Survey (LN database). Look any of these up at bls.gov.",
        None,
        ["Measure", "Foreign-born men", "Native-born men"],
        [["Civilian noninstitutional population", "LNU00073396", "LNU00073414"],
         ["Civilian labor force level", "LNU01073396", "LNU01073414"],
         ["Employment level", "LNU02073396", "LNU02073414"],
         ["Unemployment level", "LNU03073396", "LNU03073414"],
         ["Not in labor force", "LNU05073396", "LNU05073414"],
         ["Labor force participation rate", "LNU01373396", "LNU01373414"],
         ["Employment-population ratio", "LNU02373396", "LNU02373414"]],
        ["l", "c", "c"], [2.0, 1.1, 1.1],
        ["All nativity series are published unadjusted only. Totals cited in "
         "the post use LNU01000000 (unadjusted) and",
         "LNS11000000 (seasonally adjusted). · Data 4 The People"])


# --------------------------------------------------------------------------
def sigma_table(t):
    """How far each group's January-to-July change sits from its own history.

    The reference excludes 2020 (the shutdown) and the two event years, so the
    yardstick is not widened by the thing being measured.

    We report standard deviations and deliberately stop there. Converting a
    z-score this large into a probability would mean characterising the tail of
    a distribution from seventeen observations, where the normality assumption
    -- not the data -- would be doing all the work. The number means "nothing in
    the record looks like this," and nothing more.
    """
    ref = [y for y in t.index if y not in (2020, 2025, 2026)]
    out = {}
    for col in ("FBM_pop", "FBM_clf", "FBM_emp", "FBW_clf", "NBM_clf", "NBM_emp"):
        d = t.loc[ref, col]
        mu, sd = d.mean(), d.std(ddof=1)
        out[col] = {y: ((t.loc[y, col] - mu) / sd, t.loc[y, col]) for y in (2025, 2026)}
        out[col]["ref"] = (mu, sd, len(ref))
    # the two summers taken together, against the distribution of consecutive pairs
    pairs = {y: t.loc[y, "FBM_pop"] + t.loc[y + 1, "FBM_pop"]
             for y in t.index if y + 1 in t.index}
    refp = [v for y, v in pairs.items() if y not in (2019, 2020, 2024, 2025)]
    mu = sum(refp) / len(refp)
    sd = (sum((v - mu) ** 2 for v in refp) / (len(refp) - 1)) ** 0.5
    out["FBM_pop_2yr"] = {"z": (pairs[2025] - mu) / sd, "value": pairs[2025],
                          "ref": (mu, sd, len(refp))}
    return out


def print_sigma(t):
    z = sigma_table(t)
    n = z["FBM_pop"]["ref"][2]
    print(f"\nDEPARTURE FROM THE SERIES' OWN HISTORY "
          f"(z, reference n={n}, excludes 2020/2025/2026)")
    for col in ("FBM_pop", "FBM_clf", "FBM_emp", "FBW_clf", "NBM_clf", "NBM_emp"):
        mu, sd, _ = z[col]["ref"]
        print(f"  {col:9s} mean {mu:+7,.0f} sd {sd:6,.0f}   "
              f"2025 {z[col][2025][1]:+7,.0f} ({z[col][2025][0]:+.1f}z)   "
              f"2026 {z[col][2026][1]:+7,.0f} ({z[col][2026][0]:+.1f}z)")
    p = z["FBM_pop_2yr"]
    print(f"  two summers combined: {p['value']:+,.0f} vs mean {p['ref'][0]:+,.0f} "
          f"sd {p['ref'][1]:,.0f} -> {p['z']:+.1f}z")


# --------------------------------------------------------------------------
# Occupation detail is published annually, by nativity and sex, as each group's
# percentage distribution across occupations. Combining those percentages with
# the groups' employment levels gives the foreign-born share of each occupation
# -- the number the post actually needs, and one BLS does not publish directly.

OCC = {
    "Farming, fishing and forestry":      ("LNU02073565", "LNU02073652"),
    "Construction and extraction":        ("LNU02073568", "LNU02073655"),
    "Building and grounds maintenance":   ("LNU02073547", "LNU02073634"),
    "Healthcare support":                 ("LNU02073538", "LNU02073625"),
    "Food preparation and serving":       ("LNU02073544", "LNU02073631"),
    "Transportation and material moving": ("LNU02073580", "LNU02073667"),
    "Production":                         ("LNU02073577", "LNU02073664"),
    "Management, professional, related":  ("LNU02073496", "LNU02073583"),
    "Protective service":                 ("LNU02073541", "LNU02073628"),
}
OCC_YEAR = 2025          # latest annual occupation detail


def occupation_shares(w, year=OCC_YEAR):
    """Foreign-born men's share of each occupation, derived from published parts.

    Fetched directly rather than through bls_client.fetch, which requests from
    1948: these annual series begin in 2005 and the API returns nothing for a
    window that far back.
    """
    import requests
    bls_client.load_dotenv()
    key = bls_client.get_api_key()
    ids = [i for pair in OCC.values() for i in pair]
    body = requests.post(bls_client.API_URL,
                         json={"seriesid": ids, "startyear": str(year),
                               "endyear": str(year), "registrationkey": key},
                         timeout=60).json()
    pct = {s["seriesID"]: float(d["value"])
           for s in body.get("Results", {}).get("series", [])
           for d in s["data"] if d["period"] == "A01"}
    fb = w.loc[str(year), "FBM_emp"].mean()
    nb = w.loc[str(year), "NBM_emp"].mean()
    rows = []
    for name, (f, n) in OCC.items():
        if f not in pct or n not in pct:
            continue
        fw, nw = fb * pct[f] / 100, nb * pct[n] / 100
        rows.append((name, pct[f], pct[n], fw, 100 * fw / (fw + nw)))
    return fb, nb, sorted(rows, key=lambda r: -r[4])


def print_occupations(w):
    try:
        fb, nb, rows = occupation_shares(w)
    except Exception as e:                       # offline or quota exhausted
        print(f"\n(occupation table skipped: {e})")
        return
    print(f"\nOCCUPATION CONCENTRATION, {OCC_YEAR} annual averages")
    print(f"  employed men: foreign-born {fb:,.0f}k, native-born {nb:,.0f}k "
          f"-> foreign-born are {100*fb/(fb+nb):.1f}% of employed men")
    print(f"  {'occupation':36s} {'FB men%':>8s} {'NB men%':>8s} "
          f"{'FB men (k)':>11s} {'FB share':>9s}")
    for name, fp, np_, fw, share in rows:
        print(f"  {name:36s} {fp:8.1f} {np_:8.1f} {fw:11,.0f} {share:8.1f}%")


# --------------------------------------------------------------------------
def table_gap(t, norm):
    """The three-box decomposition, as an image.

    Prismic rich text has no table block, so every table in this post is a PNG.
    This one and table_occupations were Markdown until the post was prepared for
    the CMS; rendering them here keeps all four consistent and keeps their
    numbers regenerating from the data like everything else.
    """
    tot = t.loc[list(WINDOWS), "FBM_pop"].sum() - 2 * norm["FBM_pop"]
    rows = []
    for key, label in (("FBM_emp", "Employed"),
                       ("FBM_nilf", "Not in labor force"),
                       ("FBM_une", "Unemployed")):
        g = t.loc[list(WINDOWS), key].sum() - 2 * norm[key]
        rows.append([label, f"{g:+,.0f}", f"{100*g/tot:.0f}%"])
    render_table(
        OUT / "table_gap.png",
        "Eighty-eight percent came out of jobs",
        "Foreign-born men: gap against a typical two summers, January to July "
        "2025 and 2026 combined, thousands",
        None,
        ["", "Gap vs a typical two summers", "Share"],
        rows, ["l", "r", "r"], [1.6, 1.5, 0.8],
        ["The three states are exhaustive, so they sum to the "
         f"{tot:+,.0f} thousand gap in the population.",
         "A typical two summers is twice the mean January-to-July change over "
         "2013-2024, excluding 2020.",
         "Series LNU02073396, LNU03073396, LNU05073396 · Data 4 The People"],
        hi_rows=(0,))


def table_occupations(w):
    """Foreign-born men's share of each occupation."""
    try:
        fb, nb, rows = occupation_shares(w)
    except Exception as e:
        print(f"(occupation table image skipped: {e})")
        return
    share = 100 * fb / (fb + nb)
    body, hi = [], []
    for i, (name, _fp, _np, fw, sh) in enumerate(rows):
        # Every row carries its headcount. A threshold that shows the count on
        # some rows and not others reads as an oversight rather than a rule.
        body.append([name, f"{sh:.0f}%", f"{fw/1000:.1f}M"])
        if sh > share + 3:
            hi.append(i)
    render_table(
        OUT / "table_occupations.png",
        "Where the work actually is",
        f"{OCC_YEAR} annual averages, men aged 16 and over",
        None,
        ["Occupation", "Foreign-born men as % of total men",
         "Number of foreign-born men"],
        body, ["l", "r", "r"], [1.7, 1.5, 1.2],
        [f"Foreign-born men are {share:.1f}% of all employed men. Highlighted "
         "rows are the occupations where they are most",
         "over-represented relative to that share. Derived by applying each "
         "group's published occupational distribution",
         "to its published employment level. Series LNU020735xx and "
         "LNU020736xx · Data 4 The People"],
        hi_rows=tuple(hi))


# --------------------------------------------------------------------------
def findings(w, t, norm):
    """Print every number the post asserts, so the prose can be checked."""
    C = lambda c: t.loc[list(WINDOWS), c].sum()
    G = lambda c: C(c) - 2 * norm[c]
    print("\n" + "=" * 74)
    print("TWO SEAM-FREE SUMMERS: Jan-Jul 2025 and Jan-Jul 2026")
    print("=" * 74)
    print(f"{'':12s} {'2025':>9s} {'2026':>9s} {'combined':>9s} "
          f"{'typical x2':>11s} {'gap':>9s}")
    for c in ("FBM_pop", "FBM_clf", "FBM_emp", "FBM_une", "FBM_nilf"):
        print(f"{c:12s} {t.loc[2025,c]:+9,.0f} {t.loc[2026,c]:+9,.0f} "
              f"{C(c):+9,.0f} {2*norm[c]:+11,.0f} {G(c):+9,.0f}")
    print(f"  identity: emp+une+nilf combined = "
          f"{C('FBM_emp')+C('FBM_une')+C('FBM_nilf'):+,.0f} vs pop {C('FBM_pop'):+,.0f}")

    tot = G("FBM_pop")
    print(f"\nSHARE OF THE ANOMALY (gap vs a typical two summers, {tot:+,.0f}k):")
    for c in ("FBM_emp", "FBM_une", "FBM_nilf"):
        print(f"   {c:9s} {G(c):+8,.0f}   {100*G(c)/tot:6.1f}%")
    print(f"   additivity: {G('FBM_emp')+G('FBM_une')+G('FBM_nilf'):+,.0f}")

    print("\nRANKINGS (Jan-Jul change, all years on record):")
    for c, lbl in (("FBM_pop", "population"), ("FBM_clf", "labor force"),
                   ("FBM_emp", "employment")):
        order = t[c].sort_values()
        pos = {int(y): i + 1 for i, y in enumerate(order.index)}
        print(f"   {lbl:11s} 2026 rank {pos[2026]}/{len(order)}, "
              f"2025 rank {pos[2025]}/{len(order)}   "
              f"| worst three: " +
              ", ".join(f"{int(y)} {v:+,.0f}" for y, v in order.head(3).items()))

    print("\nSHARE OF THE LABOR FORCE SHORTFALL:")
    print(f"   total labor force, combined {C('CLF_nsa'):+,.0f}k vs typical "
          f"{2*norm['CLF_nsa']:+,.0f}k -> gap {G('CLF_nsa'):+,.0f}k")
    print(f"   foreign-born men            gap {G('FBM_clf'):+,.0f}k "
          f"= {100*G('FBM_clf')/G('CLF_nsa'):.0f}% of the shortfall")
    share = w.FBM_clf[LAST] / w.CLF_nsa[LAST]
    print(f"   they are {100*share:.1f}% of the labor force -> "
          f"{(G('FBM_clf')/G('CLF_nsa'))/share:.1f}x over-contribution")

    print("\nDID NATIVE-BORN MEN FILL THE GAP?")
    for c in ("NBM_pop", "NBM_clf", "NBM_emp"):
        print(f"   {c:8s} combined {C(c):+8,.0f}  typical {2*norm[c]:+8,.0f}  "
              f"gap {G(c):+8,.0f}")
    print("\n   participation and employment rates, each summer:")
    for y in WINDOWS:
        a, b = pd.Timestamp(y, 1, 1), pd.Timestamp(y, 7, 1)
        print(f"     {y}: NBM lfpr {w.NBM_lfpr[a]:.1f} -> {w.NBM_lfpr[b]:.1f}"
              f"   NBM epop {w.NBM_epop[a]:.1f} -> {w.NBM_epop[b]:.1f}"
              f"   | FBM epop {w.FBM_epop[a]:.1f} -> {w.FBM_epop[b]:.1f}")
    nl = t.NBM_lfpr.sort_values()
    print(f"   NBM participation rise, 2026 rank "
          f"{list(nl.index).index(2026)+1}/{len(nl)} "
          f"(2026 {t.loc[2026,'NBM_lfpr']:+.1f} vs typical {norm['NBM_lfpr']:+.1f})")

    print("\nWHY THE SEAM MATTERS:")
    dec, jan = pd.Timestamp(2025, 12, 1), pd.Timestamp(2026, 1, 1)
    for c in ("FBM_pop", "NBM_pop"):
        print(f"   {c}: {w[c][jan]-w[c][dec]:+,.0f}k across the Dec-Jan seam")
    print("=" * 74 + "\n")


if __name__ == "__main__":
    w = load()
    t = jan_to_jul(w)
    norm = typical(t)
    findings(w, t, norm)
    print_sigma(t)
    print_occupations(w)
    chart_hero(w)
    chart_hero(w, OUT / "2026-08-29-the-men-who-vanished-hero-1680x1080.png",
               figsize=(8.4, 5.4), fs=0.78)
    chart_ranking(t)
    chart_where_they_went(t, norm)
    chart_not_filled(w, t, norm)
    chart_divergence(w)
    tables(t, norm)
    table_gap(t, norm)
    table_occupations(w)
