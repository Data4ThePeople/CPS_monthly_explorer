#!/usr/bin/env python3
"""
Prime-age (25-54) labor force participation rate by education x sex,
from CPS basic monthly public-use FIXED-WIDTH (.dat) files.

    python cps_extract.py data/ --dicts dicts/ -o prime_age_lfpr.csv

Column positions are read from the Census data dictionary CSVs, never
hardcoded. The layout changed in June 2024 (telework variables PTTLWK/
PXTLWK inserted at 252 and 840), so you need one dictionary per era.

    dicts/
      cps_dd_2023.csv     <- covers Jan 2023 - May 2024
      cps_dd_2024.csv     <- covers Jun 2024 onward
      ...

Each dictionary is the "Data Dictionary_CSV" download from the year tab at
    https://www.census.gov/data/datasets/time-series/demo/cps/cps-basic.html

The script picks the dictionary whose record length matches the .dat file's
line length. If two dictionaries share a record length but differ in field
positions, it will warn.

NOTES
-----
pwcmpwgt has 4 implied decimal places. Divide by 10,000. The dictionary
confirms it is the composited final weight used for BLS published labor
force statistics; edited universe PRPERTYP=2 and PRTAGE 16+.

Validation: sum of pwcmpwgt/10000 over the whole file should equal the
civilian noninstitutional population 16+ (~275.2M as of mid-2026). If it
does not, the layout is wrong. Do not proceed.

There is no October 2025 file. Appropriations lapse. Do not interpolate.

Two January 2026 files exist: the corrected re-release (March 11, adjusted
2026 population controls) and the original used for the January Employment
Situation. census.gov/programs-surveys/cps/data/cps-dataset-revision-archive.html
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

WEIGHT_SCALE = 10_000.0

NEEDED = [
    "HRYEAR4", "HRMONTH", "PRPERTYP", "PRTAGE",
    "PESEX", "PEEDUCA", "PEMLR", "PWCMPWGT",
]

EDUC_BUCKETS = {
    **{c: "Less than high school diploma" for c in range(31, 39)},
    39: "High school graduate, no college",
    40: "Some college, no degree",
    41: "Associate degree",   # vocational
    42: "Associate degree",   # academic
    43: "Bachelor's degree only",
    44: "Advanced degree",    # master's
    45: "Advanced degree",    # professional
    46: "Advanced degree",    # doctoral
}

EDUC_ORDER = [
    "Less than high school diploma",
    "High school graduate, no college",
    "Some college, no degree",
    "Associate degree",
    "Bachelor's degree only",
    "Advanced degree",
]

SEX_MAP = {1: "Men", 2: "Women"}
IN_LABOR_FORCE = {1, 2, 3, 4}  # pemlr 1-2 employed, 3-4 unemployed
MIN_CELL_N = 75

RANGE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


def read_dictionary(path: Path) -> tuple[dict, int]:
    """Return {VARNAME: (start1, end1)} and the record length."""
    dd = pd.read_csv(path, encoding="utf-8-sig")
    dd.columns = [c.strip() for c in dd.columns]
    dd = dd[dd["NAME"].notna() & dd["LOCATION"].notna()]

    spec, reclen = {}, 0
    for name, loc in zip(dd["NAME"], dd["LOCATION"]):
        m = RANGE_RE.match(str(loc))
        if not m:
            continue  # '***' filler rows
        s, e = int(m.group(1)), int(m.group(2))
        spec[str(name).strip()] = (s, e)
        reclen = max(reclen, e)

    missing = [v for v in NEEDED if v not in spec]
    if missing:
        raise KeyError(f"{path.name}: dictionary missing {missing}")
    return spec, reclen


def load_dictionaries(dictdir: Path) -> dict[int, tuple[Path, dict]]:
    """Map record length -> (dictionary path, spec)."""
    out = {}
    for p in sorted(dictdir.glob("*.csv")):
        spec, reclen = read_dictionary(p)
        if reclen in out:
            prev_path, prev_spec = out[reclen]
            differing = [v for v in NEEDED if prev_spec[v] != spec[v]]
            if differing:
                sys.stderr.write(
                    f"WARNING: {p.name} and {prev_path.name} share record length "
                    f"{reclen} but differ on {differing}. Using {prev_path.name}.\n"
                )
            continue
        out[reclen] = (p, spec)
        sys.stderr.write(f"  dict {p.name}: reclen={reclen}\n")
    if not out:
        raise SystemExit(f"no dictionary CSVs found in {dictdir}")
    return out


def detect_reclen(path: Path) -> int:
    with open(path, "rb") as f:
        line = f.readline()
    return len(line.rstrip(b"\r\n"))


def load_dat(path: Path, spec: dict) -> pd.DataFrame:
    colspecs = [(spec[v][0] - 1, spec[v][1]) for v in NEEDED]
    df = pd.read_fwf(path, colspecs=colspecs, names=NEEDED, dtype=str, header=None)
    for c in NEEDED:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.columns = [c.lower() for c in df.columns]
    df["pwcmpwgt"] = df["pwcmpwgt"] / WEIGHT_SCALE
    return df


def sanity_check(df: pd.DataFrame, label: str) -> None:
    """Layout is right or it is wrong. This tells you which."""
    problems = []

    pop = df["pwcmpwgt"].sum()
    if not (2.4e8 < pop < 3.0e8):
        problems.append(f"weighted pop = {pop:,.0f}, expected ~2.5-2.8e8")

    sex = set(df["pesex"].dropna().unique())
    if not sex <= {1, 2, -1}:
        problems.append(f"pesex has unexpected values: {sorted(sex - {1, 2, -1})}")

    mlr = set(df["pemlr"].dropna().unique())
    if not mlr <= set(range(1, 8)) | {-1}:
        problems.append(f"pemlr out of range: {sorted(mlr - set(range(1, 8)) - {-1})}")

    edu = set(df["peeduca"].dropna().unique())
    if not edu <= set(range(31, 47)) | {-1}:
        problems.append(f"peeduca out of range: {sorted(edu - set(range(31, 47)) - {-1})}")

    age = df["prtage"].dropna()
    if age.max() > 85 or age[age != -1].min() < 0:
        problems.append(f"prtage range {age.min()}-{age.max()} (expect -1 or 0-85)")

    if problems:
        sys.stderr.write(f"\nLAYOUT CHECK FAILED for {label}:\n")
        for p in problems:
            sys.stderr.write(f"  - {p}\n")
        raise SystemExit(
            "Wrong dictionary for this file. Fixed-width misparse produces "
            "plausible numbers; refusing to continue."
        )


def prep(df: pd.DataFrame, label: str) -> pd.DataFrame:
    n0 = len(df)
    m = (
        (df["prpertyp"] == 2)
        & df["prtage"].between(25, 54)
        & df["pesex"].isin([1, 2])
        & df["peeduca"].between(31, 46)
        & df["pemlr"].between(1, 7)
        & (df["pwcmpwgt"] > 0)
    )
    df = df[m].copy()
    df["educ"] = df["peeduca"].map(EDUC_BUCKETS)
    df["sex"] = df["pesex"].map(SEX_MAP)
    df["in_lf"] = df["pemlr"].isin(IN_LABOR_FORCE)
    df["period"] = pd.to_datetime(dict(year=df["hryear4"], month=df["hrmonth"], day=1))
    sys.stderr.write(f"  {label}: {n0:>7,} rows -> {len(df):>7,} in universe\n")
    return df[["period", "educ", "sex", "in_lf", "pwcmpwgt"]]


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby(["period", "educ", "sex"], observed=True)
        .apply(
            lambda x: pd.Series({
                "pop": x["pwcmpwgt"].sum(),
                "lf": x.loc[x["in_lf"], "pwcmpwgt"].sum(),
                "n_unweighted": len(x),
            }),
            include_groups=False,
        )
        .reset_index()
    )
    out["lfpr"] = 100.0 * out["lf"] / out["pop"]
    out["educ"] = pd.Categorical(out["educ"], EDUC_ORDER, ordered=True)
    return out.sort_values(["period", "educ", "sex"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("datadir", type=Path)
    ap.add_argument("--dicts", type=Path, required=True,
                    help="directory of Census data dictionary CSVs, one per layout era")
    ap.add_argument("-o", "--out", type=Path, default=Path("prime_age_lfpr.csv"))
    args = ap.parse_args()

    sys.stderr.write("Loading dictionaries:\n")
    dicts = load_dictionaries(args.dicts)

    files = sorted(args.datadir.glob("*pub.dat"))
    if not files:
        sys.exit(f"no *pub.dat found in {args.datadir}")

    sys.stderr.write("\nProcessing:\n")
    frames = []
    for f in files:
        reclen = detect_reclen(f)
        if reclen not in dicts:
            raise SystemExit(
                f"{f.name}: record length {reclen} matches no dictionary "
                f"(have {sorted(dicts)}). Download the dictionary for that year."
            )
        _, spec = dicts[reclen]
        raw = load_dat(f, spec)
        sanity_check(raw, f.name)
        frames.append(prep(raw, f.name))

    df = pd.concat(frames, ignore_index=True)
    out = aggregate(df)
    out.to_csv(args.out, index=False)
    sys.stderr.write(f"\nwrote {args.out} ({len(out):,} rows)\n")

    thin = out[out["n_unweighted"] < MIN_CELL_N]
    if len(thin):
        sys.stderr.write(
            f"WARNING: {len(thin)} cells with unweighted n < {MIN_CELL_N}. "
            "Use 3- or 12-month averaging for those.\n"
        )

    tot = (
        df.groupby("period")
        .apply(
            lambda x: 100.0 * x.loc[x["in_lf"], "pwcmpwgt"].sum() / x["pwcmpwgt"].sum(),
            include_groups=False,
        )
        .rename("lfpr_25_54_total")
    )
    sys.stderr.write("\nPrime-age total LFPR (check vs LNU01300060):\n")
    sys.stderr.write(tot.to_string() + "\n")


if __name__ == "__main__":
    main()
