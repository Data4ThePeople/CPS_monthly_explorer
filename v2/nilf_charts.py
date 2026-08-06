#!/usr/bin/env python3
"""Build the four not-in-labor-force post charts from the BLS API.

Port of scripts/build_nilf_charts.py. Writes four PNGs in Data 4 The People
house format:

  1_nilf_pool.png        Not in labor force: total 16+, 65+, and prime-age 25-54
  2_participation.png    Labor force participation: 16+ vs prime-age, since 1976
  3_nilf_share.png       Not-in-labor-force share of the adult population
  4_primeage_share.png   Prime-age NILF as a share of prime-age population

ACCURACY: every plotted line is ONE published BLS series (or, for the two
share charts, one series divided by one population series -- labeled as such).
Nothing is summed or averaged across series. Each chart footnotes its series
IDs and adjustment basis so the numbers can be checked at bls.gov / FRED.

Basis notes (why the legacy script never produced chart 4): BLS publishes NO
seasonally adjusted population series -- population controls carry no seasonal
component -- and no SA NILF 25-54. The legacy chart-4 guard waited for the
nonexistent LNS10000060. Here the share charts divide by the NSA population
(the only published form, and exactly what BLS itself does when computing SA
rates), and each line that has no SA variant is labelled NSA under --sa
instead of silently mixing bases.

Run from anywhere:
    python v2/nilf_charts.py [--sa] [--start 1976] [--out DIR] [--refresh]
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client
import series_registry as reg

# ---- D4TP house palette ----
TEAL, CORAL, PAPER, GOLD = "#085041", "#712B13", "#FBFAF7", "#B8860B"
INK, GRID, MUTE = "#1d2a26", "#e6e2d6", "#5b6763"


def basis(sid: str) -> str:
    return "SA" if sid and sid.startswith("LNS") else "NSA"


def get(data, sid):
    g = data[data["series_id"] == sid].sort_values("date")
    return g[["date", "value"]]


def since(g, year):
    return g[g["date"] >= pd.Timestamp(year, 1, 1)]


def style_ax(ax):
    ax.set_facecolor(PAPER)
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.grid(axis="x", visible=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTE, labelsize=10)


def endlabel(ax, dates, vals, color, pct=False):
    if len(dates) == 0 or len(vals) == 0:
        return
    x, y = dates[-1], vals[-1]
    ax.scatter([x], [y], color=color, s=32, zorder=6)
    txt = f"{y:.1f}%" if pct else f"{y:,.0f}"
    ax.annotate(txt, (x, y), xytext=(8, 0), textcoords="offset points",
                color=color, fontweight="bold", fontsize=11, va="center")


def fig_setup(title, subtitle):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    fig.patch.set_facecolor(PAPER)
    fig.text(0.055, 0.955, "DATA 4 THE PEOPLE", color=GOLD, fontsize=9.5,
             fontweight="bold", family="DejaVu Sans", va="top",
             fontstretch="expanded")
    fig.text(0.055, 0.905, title, color=TEAL, fontsize=19, va="top",
             family="DejaVu Serif", fontweight="bold")
    fig.text(0.055, 0.855, subtitle, color=MUTE, fontsize=11, va="top",
             family="DejaVu Sans")
    return fig, ax


def footer(fig, sources):
    text = ("Source: U.S. Bureau of Labor Statistics, Current Population "
            "Survey (LN database). " + sources)
    lines = textwrap.wrap(text, 132)
    if len(lines) <= 1:
        y_src, y_acc = [0.045], 0.012
    else:
        y_src, y_acc = [0.066, 0.041], 0.012
    for y, line in zip(y_src, lines):
        fig.text(0.055, y, line, color=GOLD, fontsize=8.3, va="top",
                 family="DejaVu Sans")
    fig.text(0.055, y_acc,
             "One published BLS series per line — no values combined or "
             "averaged. Chart: Data 4 The People.",
             color=MUTE, fontsize=8, va="top", family="DejaVu Sans")


def share_frame(data, num_id, den_id, start_year):
    """One series divided by one population series, month-matched."""
    m = get(data, num_id).merge(get(data, den_id), on="date",
                                suffixes=("_n", "_p"))
    m["share"] = m["value_n"] / m["value_p"] * 100
    return since(m, start_year)


def main():
    ap = argparse.ArgumentParser(
        description="Build the four not-in-labor-force post charts "
                    "(D4TP house format) from the BLS API.")
    ap.add_argument("--out", default=None,
                    help="output directory (default <repo>/v2/output/post_charts)")
    ap.add_argument("--sa", action="store_true",
                    help="prefer seasonally adjusted where a SA series exists; "
                         "NSA-only lines are labelled as such")
    ap.add_argument("--start", type=int, default=1976,
                    help="first year to plot (default 1976)")
    bls_client.add_client_args(ap)
    args = ap.parse_args()

    out = Path(args.out).expanduser() if args.out else \
        bls_client.OUT_DIR / "post_charts"
    out.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {len(reg.NILF_CHART_IDS)} registry series ...")
    data = bls_client.fetch(reg.NILF_CHART_IDS, refresh=args.refresh)
    present = set(data["series_id"].unique())

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    written = []

    def pick(*ids):
        for i in ids:
            if i in present:
                return i
        return None

    # ---------- CHART 1: NILF pool ----------
    if args.sa:
        nilf_total = pick(reg.NILF_TOTAL_SA, reg.NILF_TOTAL_NSA)
    else:
        nilf_total = pick(reg.NILF_TOTAL_NSA, reg.NILF_TOTAL_SA)
    nilf_65 = pick(reg.NILF_65_NSA)     # NSA only
    nilf_25 = pick(reg.NILF_2554_NSA)   # NSA only
    if nilf_total:
        fig, ax = fig_setup("The pool that keeps growing",
                            "Americans not in the labor force, in thousands, "
                            "monthly")
        style_ax(ax)
        lines = [(nilf_total, "All adults (16+)", TEAL, 2.4),
                 (nilf_65, "65 and over", CORAL, 2.0),
                 (nilf_25, "Prime age (25–54)", GOLD, 2.0)]
        bases = {basis(sid) for sid, *_ in lines if sid}
        mixed = len(bases) > 1
        used = []
        for sid, lab, col, lw in lines:
            if not sid:
                continue
            g = since(get(data, sid), args.start)
            if g.empty:
                print(f"NOTE: {sid} has no data from {args.start}; line skipped.")
                continue
            if mixed:
                lab = f"{lab} ({basis(sid)})"
            ax.plot(g["date"], g["value"], color=col, lw=lw, label=lab)
            endlabel(ax, g["date"].values, g["value"].values, col)
            used.append(f"{sid} ({basis(sid)})" if mixed else sid)
        ax.legend(frameon=False, loc="upper left", fontsize=10,
                  labelcolor=INK)
        ax.set_ylabel("Thousands of persons", color=MUTE, fontsize=10)
        adj_note = "" if mixed else \
            (" Seasonally adjusted." if basis(nilf_total) == "SA"
             else " Not seasonally adjusted.")
        footer(fig, "Series: " + ", ".join(used) + "." + adj_note)
        fig.subplots_adjust(left=0.10, right=0.93, top=0.80, bottom=0.16)
        p = out / "1_nilf_pool.png"
        fig.savefig(p, dpi=200, facecolor=PAPER)
        plt.close(fig)
        written.append(p)
    else:
        print(f"NOTE: no NILF total series ({reg.NILF_TOTAL_NSA}/"
              f"{reg.NILF_TOTAL_SA}) returned data; skipped chart 1.")

    # ---------- CHART 2: Participation ----------
    if reg.LFPR_16_SA in present:
        fig, ax = fig_setup("Back to 1976",
                            "Labor force participation rate, percent, monthly")
        style_ax(ax)
        used = []
        for sid, lab, col in [(reg.LFPR_16_SA, "All adults (16+)", TEAL),
                              (reg.LFPR_2554_SA, "Prime age (25–54)", CORAL)]:
            if sid not in present:
                print(f"NOTE: {sid} returned no data; line skipped.")
                continue
            g = since(get(data, sid), args.start)
            ax.plot(g["date"], g["value"], color=col, lw=2.3, label=lab)
            endlabel(ax, g["date"].values, g["value"].values, col, pct=True)
            used.append(sid)
        ax.legend(frameon=False, loc="lower left", fontsize=10,
                  labelcolor=INK)
        ax.set_ylabel("Percent", color=MUTE, fontsize=10)
        footer(fig, "Seasonally adjusted. Series: " + ", ".join(used) + ".")
        fig.subplots_adjust(left=0.09, right=0.93, top=0.80, bottom=0.16)
        p = out / "2_participation.png"
        fig.savefig(p, dpi=200, facecolor=PAPER)
        plt.close(fig)
        written.append(p)
    else:
        print(f"NOTE: {reg.LFPR_16_SA} returned no data; skipped chart 2.")

    # ---------- CHART 3: NILF share of adult population ----------
    # share = NILF_total / POP_16 * 100. The denominator is the NSA population
    # (the only published form; population controls have no seasonal
    # component), so the share's basis is the numerator's basis.
    if nilf_total and reg.POP_16_NSA in present:
        m = share_frame(data, nilf_total, reg.POP_16_NSA, args.start)
        fig, ax = fig_setup("The unemployment rate's blind spot",
                            "Share of the adult population (16+) not in the "
                            "labor force, percent")
        style_ax(ax)
        ax.plot(m["date"], m["share"], color=TEAL, lw=2.4)
        endlabel(ax, m["date"].values, m["share"].values, CORAL, pct=True)
        ax.set_ylabel("Percent of population", color=MUTE, fontsize=10)
        b = basis(nilf_total)
        footer(fig, f"Share = not in labor force ({nilf_total}, {b}) ÷ "
                    f"civilian noninstitutional population ({reg.POP_16_NSA}; "
                    f"population is published unadjusted only). Equals 100 "
                    f"minus the {b} participation rate.")
        fig.subplots_adjust(left=0.10, right=0.93, top=0.80, bottom=0.17)
        p = out / "3_nilf_share.png"
        fig.savefig(p, dpi=200, facecolor=PAPER)
        plt.close(fig)
        written.append(p)
    else:
        print(f"NOTE: NILF total or population ({reg.POP_16_NSA}) missing; "
              f"skipped chart 3.")

    # ---------- CHART 4: Prime-age NILF as share of prime-age pop ----------
    # Both sides NSA (neither is published SA): honest 25-54 over 25-54.
    if nilf_25 and reg.POP_2554_NSA in present:
        m = share_frame(data, nilf_25, reg.POP_2554_NSA, args.start)
        fig, ax = fig_setup("Prime age, leaving the count",
                            "Share of adults 25–54 not in the labor force, "
                            "percent")
        style_ax(ax)
        ax.plot(m["date"], m["share"], color=TEAL, lw=2.4)
        endlabel(ax, m["date"].values, m["share"].values, CORAL, pct=True)
        ax.set_ylabel("Percent of 25–54 population", color=MUTE,
                      fontsize=10)
        footer(fig, f"Share = prime-age not in labor force ({nilf_25}) ÷ "
                    f"prime-age population ({reg.POP_2554_NSA}). Both not "
                    f"seasonally adjusted (neither is published SA).")
        fig.subplots_adjust(left=0.10, right=0.93, top=0.80, bottom=0.17)
        p = out / "4_primeage_share.png"
        fig.savefig(p, dpi=200, facecolor=PAPER)
        plt.close(fig)
        written.append(p)
    else:
        missing = [sid for sid in (nilf_25 or reg.NILF_2554_NSA,
                                   reg.POP_2554_NSA) if sid not in present]
        print(f"NOTE: skipped chart 4; no data for: {', '.join(missing)}.")

    print("\nWrote:")
    for p in written:
        print("  ", p)
    if not written:
        print("  (nothing -- check the [bls_client] messages above for "
              "series that returned no data.)")


if __name__ == "__main__":
    main()
