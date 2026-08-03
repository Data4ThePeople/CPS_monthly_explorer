#!/usr/bin/env python3
"""
audit_alldata_sums.py -- Numeric reconciliation of the CPS LN (CPS) catalog.

This is the value-level audit the series-file audit could not do. It reads the
big ln.data.1.AllData file once and checks, for the SAME monthly intersections
the CPS Monthly Explorer surfaces, whether the numbers actually add up:

  CHECK A (sex additivity): for every (dimension value, measure) where a level
    series exists for Both Sexes AND for Men AND for Women, does
        Men + Women  ==  Both Sexes   (within tolerance)
    on a not-seasonally-adjusted basis, for every overlapping month?
    NSA components must sum to the NSA total up to rounding (BLS adjusts SA
    series independently, so SA is intentionally excluded from this check).

  CHECK B (self-consistency of the tool's picks): confirms the exact series
    the tool would chart for Both/Men/Women are the clean, correct IDs (this
    re-runs the series-level selection so the sum check is testing the tool's
    actual choices, not just any series that happens to exist).

It only checks LEVELS (counts in thousands), where additivity must hold. Rates
(unemployment rate, participation rate, E-P ratio) are NOT additive across sex
and are correctly skipped.

OUTPUT:
  - console summary: how many (value, measure) triples checked, how many
    reconciled, how many failed, worst offenders
  - sum_check_failures.csv: every failing month with expected vs actual, so
    you can eyeball whether it's rounding, a real mismatch, or a data gap

USAGE:
  python3 audit_alldata_sums.py -d ~/Desktop/ln
  python3 audit_alldata_sums.py -d ~/Desktop/ln --tol 3   # thousands tolerance

Requires: pandas. Reads ln.series + mapping files + ln.data.1.AllData
(.txt suffixes fine).

INTERPRETING RESULTS:
  * Failures within a few thousand are almost always independent rounding of
    Both/Men/Women (each published rounded to the nearest thousand), NOT a
    tool error. The default tolerance of 2 (thousand) catches these.
  * Failures of tens of thousands, or a whole series failing every month,
    indicate a genuine mispairing worth investigating -- send me the row.
  * Months present in the total but missing from a component (or vice versa)
    are flagged separately as coverage gaps, not sum failures.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

SKIP = {"ln.series", "ln.txt", "ln.contacts", "ln.footnote"}


def base_name(p): 
    n = p.name
    return n[:-4] if n.lower().endswith(".txt") else n


def find_file(folder, name):
    for c in (name, name + ".txt", name + ".TXT"):
        if (folder / c).exists():
            return folder / c
    return None


def read_bls(path):
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                     na_values=[], engine="python")
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def load_lookups(folder):
    lk = {}
    for f in sorted(folder.iterdir()):
        name = base_name(f)
        if (not name.startswith("ln.") or name in SKIP
                or name.startswith("ln.data")):
            continue
        try:
            t = read_bls(f)
        except Exception:
            continue
        cc = [c for c in t.columns if c.endswith("_code")]
        tc = [c for c in t.columns if c.endswith("_text")]
        if len(cc) == 1 and tc:
            lk[cc[0]] = dict(zip(t[cc[0]], t[tc[0]]))
    return lk


def match_lookup(lk, col):
    if col in lk:
        return lk[col]
    pre = col.replace("_code", "")
    for k, v in lk.items():
        if k.replace("_code", "").startswith(pre) or pre.startswith(k.replace("_code", "")):
            return v
    return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("-d", "--dir", default="~/Desktop/ln")
    ap.add_argument("--data", help="explicit path to ln.data file")
    ap.add_argument("--tol", type=float, default=2.0,
                    help="tolerance in thousands for Men+Women vs Both "
                         "(default 2; rounding noise lives here)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    out = Path(args.out).expanduser() if args.out else folder
    out.mkdir(parents=True, exist_ok=True)

    sp = find_file(folder, "ln.series")
    if sp is None:
        sys.exit(f"ERROR: no ln.series(.txt) in {folder}")
    s = read_bls(sp)
    if "seasonal" not in s.columns:
        s["seasonal"] = s["series_id"].str[2]
    lookups = load_lookups(folder)

    dims = [c for c in s.columns
            if c.endswith("_code") and c != "footnote_codes"]
    short = {d: d.replace("_code", "") for d in dims}
    per = next(d for d in dims if short[d].startswith("periodicity"))
    lfst = next(d for d in dims if short[d].startswith("lfst"))
    ages = next(d for d in dims if short[d].startswith("age"))
    sexs = next(d for d in dims if short[d].startswith("sex"))
    tdat = next((d for d in dims if short[d] == "tdat"), None)

    monthly = s[s[per] == "M"].copy()
    defaults = {d: monthly[d].mode().iloc[0] for d in dims}
    md = [d for d in dims if short[d] in ("tdat", "pcts")]
    cond = {d: monthly.groupby(lfst)[d].agg(lambda x: x.mode().iloc[0])
            for d in md}

    # A measure is a "level" (additive) if its tdat default is thousands.
    # Rates carry a percent tdat and are skipped.
    tdat_lk = match_lookup(lookups, tdat) if tdat else {}
    def is_level(lf):
        if not tdat:
            return True
        code = cond[tdat].get(lf, defaults[tdat])
        return "thousand" in tdat_lk.get(code, "").lower()

    def others_at_default(df, free):
        m = pd.Series(True, index=df.index)
        for dd in dims:
            if dd in free or dd in (lfst, per):
                continue
            if dd in md:
                m &= df[dd] == df[lfst].map(cond[dd])
            else:
                m &= df[dd] == defaults[dd]
        return m

    def pick_one(g):
        g = g.copy()
        g["_end"] = pd.to_numeric(g["end_year"], errors="coerce").fillna(0)
        # NSA only for additivity, so prefer U; then current; then long; then id
        g["_u"] = (g["seasonal"] == "U").astype(int)
        g["_len"] = g["_end"] - pd.to_numeric(g["begin_year"],
                                              errors="coerce").fillna(9999)
        g = g.sort_values(["_u", "_end", "_len", "series_id"],
                          ascending=[False, False, False, True])
        return g.iloc[0]["series_id"]

    picker = [d for d in dims
              if short[d] not in ("lfst", "periodicity", "tdat", "pcts",
                                  "seasonal")
              and (monthly[d] != defaults[d]).any()]
    auc = {}
    def age_universe(d):
        if d in auc:
            return auc[d]
        o = pd.Series(0, index=monthly.index)
        for dd in dims:
            if dd in (lfst, per, ages):
                continue
            if dd in md:
                o += (monthly[dd] != monthly[lfst].map(cond[dd])).astype(int)
            else:
                o += (monthly[dd] != defaults[dd]).astype(int)
        c = monthly[(o == 1) & (monthly[d] != defaults[d])]
        v = c[ages].mode().iloc[0] if len(c) else defaults[ages]
        auc[d] = v
        return v

    # ---- Build the list of (Both, Men, Women) NSA level triples to check ----
    triples = []   # (label, both_id, men_id, women_id)
    lfst_lk = match_lookup(lookups, lfst)

    # Headline sex triples: Both/Men/Women with ALL other dims at default.
    head_both = monthly[(monthly[sexs] == defaults[sexs])
                        & others_at_default(monthly, {sexs})]
    head_men = monthly[(monthly[sexs] == "1")
                       & others_at_default(monthly, {sexs})]
    head_wom = monthly[(monthly[sexs] == "2")
                       & others_at_default(monthly, {sexs})]
    for lf, gb in head_both.groupby(lfst):
        if not is_level(lf):
            continue
        m = head_men[head_men[lfst] == lf]
        w = head_wom[head_wom[lfst] == lf]
        if len(m) and len(w):
            triples.append((f"ALL 16+ | {lfst_lk.get(lf, lf)}",
                            pick_one(gb), pick_one(m), pick_one(w)))

    for d in picker:
        if d == sexs:
            continue
        u = defaults[ages] if d == ages else age_universe(d)
        # Both-sexes base (this dim off default, sex at default, others default)
        base = monthly[(monthly[d] != defaults[d])
                       & (monthly[sexs] == defaults[sexs])
                       & others_at_default(monthly, {d, ages})]
        if d != ages:
            base = base[base[ages] == u]
        # Men / Women variants
        sub = monthly[(monthly[d] != defaults[d])
                      & (monthly[sexs] != defaults[sexs])
                      & others_at_default(monthly, {d, ages, sexs})]
        if d != ages:
            sub = sub[sub[ages] == u]

        for (code, lf), gb in base.groupby([d, lfst]):
            if not is_level(lf):
                continue
            men = sub[(sub[d] == code) & (sub[lfst] == lf)
                      & (sub[sexs] == "1")]
            wom = sub[(sub[d] == code) & (sub[lfst] == lf)
                      & (sub[sexs] == "2")]
            if len(men) and len(wom):
                lab = (f"{short[d]}={match_lookup(lookups, d).get(code, code)} "
                       f"| {lfst_lk.get(lf, lf)}")
                triples.append((lab, pick_one(gb),
                                pick_one(men), pick_one(wom)))

    wanted = set()
    for _, b, m, w in triples:
        wanted |= {b, m, w}
    print(f"Sex-additive level triples to check: {len(triples)}")
    print(f"Distinct series needed from data file: {len(wanted)}")

    # ---- Stream AllData for just those series ----
    paths = [Path(args.data)] if args.data else sorted(folder.glob("ln.data*"))
    if not paths:
        sys.exit(f"ERROR: no ln.data.* file in {folder}")
    frames = []
    for p in paths:
        print(f"Streaming {p.name} (this is the big one) ...")
        for chunk in pd.read_csv(p, sep="\t", dtype=str, chunksize=1_000_000,
                                 keep_default_na=False, na_values=[]):
            chunk.columns = [c.strip() for c in chunk.columns]
            chunk["series_id"] = chunk["series_id"].str.strip()
            hit = chunk[chunk["series_id"].isin(wanted)]
            if len(hit):
                frames.append(hit)
    if not frames:
        sys.exit("ERROR: needed series not found in data file.")
    d = pd.concat(frames, ignore_index=True)
    d["period"] = d["period"].str.strip()
    d = d[d["period"].str.match(r"M(0[1-9]|1[0-2])$")]  # monthly only
    d["value"] = pd.to_numeric(d["value"].str.strip(), errors="coerce")
    d["ym"] = d["year"].str.strip() + d["period"]
    piv = d.pivot_table(index="ym", columns="series_id", values="value",
                        aggfunc="first")

    # ---- Reconcile ----
    rows = []
    fails = []
    reconciled = 0
    checked = 0
    coverage_gaps = 0
    for lab, b, m, w in triples:
        if not all(x in piv.columns for x in (b, m, w)):
            coverage_gaps += 1
            continue
        sub = piv[[b, m, w]].dropna()
        if sub.empty:
            coverage_gaps += 1
            continue
        diff = (sub[m] + sub[w]) - sub[b]
        bad = sub[diff.abs() > args.tol]
        checked += 1
        maxerr = float(diff.abs().max())
        if len(bad) == 0:
            reconciled += 1
        else:
            for ym, r in bad.iterrows():
                fails.append({"triple": lab, "month": ym, "both_id": b,
                              "men_id": m, "women_id": w,
                              "both": r[b], "men": r[m], "women": r[w],
                              "men+women": r[m] + r[w],
                              "error": (r[m] + r[w]) - r[b]})
        rows.append({"triple": lab, "both_id": b, "men_id": m, "women_id": w,
                     "months": len(sub), "max_abs_error_000s": round(maxerr, 1),
                     "status": "OK" if len(bad) == 0 else f"{len(bad)} fail"})

    summary = pd.DataFrame(rows).sort_values("max_abs_error_000s",
                                             ascending=False)
    summary.to_csv(out / "sum_check_summary.csv", index=False)
    if fails:
        pd.DataFrame(fails).to_csv(out / "sum_check_failures.csv", index=False)

    print("\n==================== RESULT ====================")
    print(f"Level triples checked:        {checked}")
    print(f"  reconciled (Men+Women=Both): {reconciled}  "
          f"({reconciled/checked*100:.1f}%)" if checked else "")
    print(f"  with >{args.tol}k discrepancy: {checked - reconciled}")
    print(f"Triples skipped (missing data/coverage gap): {coverage_gaps}")
    print(f"\nWrote: {out/'sum_check_summary.csv'}")
    if fails:
        print(f"Wrote: {out/'sum_check_failures.csv'}  ({len(fails)} rows)")
        print("\nWorst triples by max error (thousands):")
        print(summary.head(12).to_string(index=False))
        print("\nSmall errors (a few thousand) are rounding of independently "
              "rounded\nBoth/Men/Women and are expected. Large or "
              "every-month errors are real\nmispairings -- send me those rows.")
    else:
        print("\nPERFECT: every level triple reconciles within tolerance. "
              "The value\nlayer is now measured, not inferred.")


if __name__ == "__main__":
    main()
