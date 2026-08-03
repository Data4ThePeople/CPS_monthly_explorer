#!/usr/bin/env python3
"""
build_nilf_charts.py -- Build the four charts for the "It's Time to Move On
From the Unemployment Rate" post, straight from the local BLS LN (CPS) files.

Reads ln.series + ln.data.* from a folder (default ~/Desktop/ln, .txt suffixes
fine) and writes four PNGs in Data 4 The People house format:

  1_nilf_pool.png        Not in labor force: total 16+, 65+, and prime-age 25-54
  2_participation.png    Labor force participation: 16+ vs prime-age, since 1976
  3_nilf_share.png       Not-in-labor-force share of the adult population
  4_primeage_share.png   Prime-age not in labor force as a share of prime-age pop

ACCURACY: every plotted line is ONE published BLS series (or, for the two
share charts, one series divided by one population series -- labeled as such).
Nothing is summed or averaged across series. Each chart footnotes its series
IDs so the numbers can be checked at bls.gov / FRED.

USAGE:
  python3 build_nilf_charts.py -d ~/Desktop/ln
  python3 build_nilf_charts.py -d ~/Desktop/ln --sa        # prefer seas.-adj.
  python3 build_nilf_charts.py -d ~/Desktop/ln --out ~/Desktop/charts

The series IDs below are the standard CPS/LN codes. If any is absent in your
files (some are SA-only or NSA-only), the script says so and skips that line
rather than guessing. Verify IDs it reports against your explorer footer.

Requires: pandas, matplotlib.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# ---- D4TP house palette ----
TEAL, CORAL, PAPER, GOLD = "#085041", "#712B13", "#FBFAF7", "#B8860B"
INK, GRID, MUTE = "#1d2a26", "#e6e2d6", "#5b6763"

# ---- Series we need (standard CPS/LN codes) ----
# Levels are in thousands; rates are percent.
NILF_TOTAL_SA, NILF_TOTAL_NSA = "LNS15000000", "LNU05000000"
NILF_65_NSA = "LNU05000097"          # 65+ is published NSA
NILF_2554_SA, NILF_2554_NSA = "LNS15000060", "LNU05000060"
LFPR_16_SA = "LNS11300000"
LFPR_2554_SA = "LNS11300060"
POP_16_SA, POP_16_NSA = "LNS10000000", "LNU00000000"
POP_2554_SA = "LNS10000060"

MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def find_file(folder, name):
    for c in (name, name + ".txt", name + ".TXT"):
        if (folder / c).exists():
            return folder / c
    return None


def load_series_meta(folder):
    sp = find_file(folder, "ln.series")
    if sp is None:
        sys.exit(f"ERROR: no ln.series(.txt) in {folder}")
    df = pd.read_csv(sp, sep="\t", dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    df["series_id"] = df["series_id"].str.strip()
    return set(df["series_id"])


def load_data(folder, wanted):
    paths = sorted(folder.glob("ln.data*"))
    if not paths:
        sys.exit(f"ERROR: no ln.data.* file in {folder}")
    frames = []
    for p in paths:
        print(f"  streaming {p.name} ...")
        for chunk in pd.read_csv(p, sep="\t", dtype=str, chunksize=1_000_000,
                                 keep_default_na=False, na_values=[]):
            chunk.columns = [c.strip() for c in chunk.columns]
            chunk["series_id"] = chunk["series_id"].str.strip()
            hit = chunk[chunk["series_id"].isin(wanted)]
            if len(hit):
                frames.append(hit)
    if not frames:
        sys.exit("ERROR: none of the needed series were found in the data.")
    d = pd.concat(frames, ignore_index=True)
    d["period"] = d["period"].str.strip()
    d = d[d["period"].str.match(r"M(0[1-9]|1[0-2])$")]
    d["value"] = pd.to_numeric(d["value"].str.strip(), errors="coerce")
    d["date"] = pd.to_datetime(d["year"].str.strip() + "-"
                               + d["period"].str[1:] + "-01")
    return d.dropna(subset=["value"])[["series_id", "date", "value"]]


def pick(available, *ids):
    """Return the first id that exists in the data, else None."""
    for i in ids:
        if i in available:
            return i
    return None


def get(data, sid):
    g = data[data["series_id"] == sid].sort_values("date")
    return g["date"].values, g["value"].values, g


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
    fig.text(0.055, 0.045,
             "Source: U.S. Bureau of Labor Statistics, Current Population "
             "Survey (LN database). " + sources,
             color=GOLD, fontsize=8.3, va="top", family="DejaVu Sans")
    fig.text(0.055, 0.012,
             "One published BLS series per line \u2014 no values combined or "
             "averaged. Chart: Data 4 The People.",
             color=MUTE, fontsize=8, va="top", family="DejaVu Sans")


def since(g, year):
    return g[g["date"] >= pd.Timestamp(year, 1, 1)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("-d", "--dir", default="~/Desktop/ln")
    ap.add_argument("--out", default=None)
    ap.add_argument("--sa", action="store_true",
                    help="prefer seasonally adjusted where available")
    ap.add_argument("--start", type=int, default=1976,
                    help="first year to plot (default 1976)")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    out = Path(args.out).expanduser() if args.out else folder / "post_charts"
    out.mkdir(parents=True, exist_ok=True)

    avail_meta = load_series_meta(folder)
    all_ids = {NILF_TOTAL_SA, NILF_TOTAL_NSA, NILF_65_NSA, NILF_2554_SA,
               NILF_2554_NSA, LFPR_16_SA, LFPR_2554_SA, POP_16_SA, POP_16_NSA,
               POP_2554_SA}
    all_ids = {i for i in all_ids if i in avail_meta}
    print(f"Series present in your files: {len(all_ids)} of 10 candidates")
    print("Loading data (this reads the big data file once) ...")
    data = load_data(folder, all_ids)
    present = set(data["series_id"].unique())

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    written = []

    # ---------- CHART 1: NILF pool ----------
    nilf_total = pick(present, NILF_TOTAL_NSA, NILF_TOTAL_SA) if not args.sa \
        else pick(present, NILF_TOTAL_SA, NILF_TOTAL_NSA)
    nilf_65 = pick(present, NILF_65_NSA)
    nilf_25 = pick(present, NILF_2554_NSA, NILF_2554_SA) if not args.sa \
        else pick(present, NILF_2554_SA, NILF_2554_NSA)
    if nilf_total:
        fig, ax = fig_setup("The pool that keeps growing",
                            "Americans not in the labor force, in thousands, "
                            "monthly")
        style_ax(ax)
        lines = [(nilf_total, "All adults (16+)", TEAL, 2.4),
                 (nilf_65, "65 and over", CORAL, 2.0),
                 (nilf_25, "Prime age (25\u201354)", GOLD, 2.0)]
        used = []
        for sid, lab, col, lw in lines:
            if not sid:
                continue
            x, y, g = get(data, sid)
            g = since(g, args.start)
            ax.plot(g["date"], g["value"], color=col, lw=lw, label=lab)
            endlabel(ax, g["date"].values, g["value"].values, col)
            used.append(sid)
        ax.legend(frameon=False, loc="upper left", fontsize=10,
                  labelcolor=INK)
        ax.set_ylabel("Thousands of persons", color=MUTE, fontsize=10)
        footer(fig, "Series: " + ", ".join(used) + ".")
        fig.subplots_adjust(left=0.10, right=0.93, top=0.80, bottom=0.16)
        p = out / "1_nilf_pool.png"
        fig.savefig(p, dpi=200, facecolor=PAPER)
        plt.close(fig)
        written.append(p)

    # ---------- CHART 2: Participation ----------
    if LFPR_16_SA in present:
        fig, ax = fig_setup("Back to 1976",
                            "Labor force participation rate, percent, monthly")
        style_ax(ax)
        used = []
        for sid, lab, col in [(LFPR_16_SA, "All adults (16+)", TEAL),
                              (LFPR_2554_SA, "Prime age (25\u201354)", CORAL)]:
            if sid not in present:
                continue
            x, y, g = get(data, sid)
            g = since(g, args.start)
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

    # ---------- CHART 3: NILF share of adult population ----------
    # share = NILF_total / POP_16 * 100  (== 100 - LFPR, shown as the mirror)
    pop16 = pick(present, POP_16_SA, POP_16_NSA)
    if nilf_total and pop16:
        _, _, gn = get(data, nilf_total)
        _, _, gp = get(data, pop16)
        m = gn.merge(gp, on="date", suffixes=("_n", "_p"))
        m["share"] = m["value_n"] / m["value_p"] * 100
        m = m[m["date"] >= pd.Timestamp(args.start, 1, 1)]
        fig, ax = fig_setup("The unemployment rate's blind spot",
                            "Share of the adult population (16+) not in the "
                            "labor force, percent")
        style_ax(ax)
        ax.plot(m["date"], m["share"], color=TEAL, lw=2.4)
        endlabel(ax, m["date"].values, m["share"].values, CORAL, pct=True)
        ax.set_ylabel("Percent of population", color=MUTE, fontsize=10)
        footer(fig, f"Share = not in labor force ({nilf_total}) \u00f7 civilian "
                    f"noninstitutional population ({pop16}). Mirror of the "
                    f"participation rate.")
        fig.subplots_adjust(left=0.10, right=0.93, top=0.80, bottom=0.17)
        p = out / "3_nilf_share.png"
        fig.savefig(p, dpi=200, facecolor=PAPER)
        plt.close(fig)
        written.append(p)

    # ---------- CHART 4: Prime-age NILF as share of prime-age pop ----------
    # = 100 - prime-age LFPR. Cleanest, honest denominator (25-54 over 25-54).
    if nilf_25 and POP_2554_SA in present:
        _, _, gn = get(data, nilf_25)
        _, _, gp = get(data, POP_2554_SA)
        m = gn.merge(gp, on="date", suffixes=("_n", "_p"))
        m["share"] = m["value_n"] / m["value_p"] * 100
        m = m[m["date"] >= pd.Timestamp(args.start, 1, 1)]
        fig, ax = fig_setup("Prime age, leaving the count",
                            "Share of adults 25\u201354 not in the labor force, "
                            "percent")
        style_ax(ax)
        ax.plot(m["date"], m["share"], color=TEAL, lw=2.4)
        endlabel(ax, m["date"].values, m["share"].values, CORAL, pct=True)
        ax.set_ylabel("Percent of 25\u201354 population", color=MUTE,
                      fontsize=10)
        footer(fig, f"Share = prime-age not in labor force ({nilf_25}) \u00f7 "
                    f"prime-age population ({POP_2554_SA}).")
        fig.subplots_adjust(left=0.10, right=0.93, top=0.80, bottom=0.17)
        p = out / "4_primeage_share.png"
        fig.savefig(p, dpi=200, facecolor=PAPER)
        plt.close(fig)
        written.append(p)
    elif nilf_25:
        print("NOTE: prime-age population series (LNS10000060) not found; "
              "skipped chart 4. You can instead plot 100 - prime-age LFPR "
              "from chart 2's second line.")

    print("\nWrote:")
    for p in written:
        print("  ", p)
    if not written:
        print("  (nothing -- check that the series IDs above exist in your "
              "files; the explorer footer shows the exact IDs.)")


if __name__ == "__main__":
    main()
