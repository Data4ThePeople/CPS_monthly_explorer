#!/usr/bin/env python3
"""
explore_ln.py -- Explore the BLS LN (Current Population Survey) series catalog.

The key insight: ln.series IS the catalog of what exists. Every row is one
published series, and its dimension codes (born_code, sexs_code, ages_code,
lfst_code, etc.) tell you exactly which intersection of variables it covers.
If a combination has no row in ln.series, BLS simply does not publish it --
that is why some intersections in Tableau come up empty.

You do NOT need the big ln.data files to answer "what exists?" questions.
Point this script at a folder containing ln.series plus the small mapping
files (ln.sexs, ln.born, ln.ages, ln.lfst, ...) downloaded from
https://download.bls.gov/pub/time.series/ln/

USAGE (run from terminal):

  python explore_ln.py -d ~/Desktop/ln dims
      List every dimension and how many distinct codes are actually used.

  python explore_ln.py -d ~/Desktop/ln values born
      Show the codes/labels for one dimension and how many series use each.

  python explore_ln.py -d ~/Desktop/ln profile --filter born=native
      For all series matching the filter(s): which dimensions VARY (data
      exists at multiple values) vs. which are FIXED. This is the fastest
      way to see "given native-born, what can I slice by?"

  python explore_ln.py -d ~/Desktop/ln cross sexs ages --filter born=native
      Series-count crosstab of two dimensions, under optional filters.
      Zeros/blanks = that intersection is not published.

  python explore_ln.py -d ~/Desktop/ln find --filter born=native --filter sexs=men --title "labor force" --limit 40
      List actual series IDs + titles + date ranges matching filters.

  python explore_ln.py -d ~/Desktop/ln series LNU02073395
      Fully decode a single series ID across every dimension.

FILTER SYNTAX:  --filter dim=value   (repeatable)
  * dim can be shorthand: born, sexs, ages, lfst, race, orig, education,
    indy, occ, periodicity, seasonal ... ('_code' suffix optional)
  * value matches a code exactly (e.g. sexs=1) OR a label substring,
    case-insensitive (e.g. sexs=men, born=native, lfst="labor force").
  * seasonal is derived from the 3rd character of the series ID when the
    file lacks a column: S = seasonally adjusted, U = not adjusted.
  * add --active to keep only series still being published (max end_year).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

pd.set_option("display.max_rows", 1000)
pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 95)

SKIP_FILES = {"ln.series", "ln.txt", "ln.contacts", "ln.footnote"}


def base_name(path: Path) -> str:
    """Filename with any trailing '.txt' stripped (browsers add it)."""
    n = path.name
    return n[:-4] if n.lower().endswith(".txt") else n


def find_file(folder: Path, name: str):
    """Locate a BLS file whether saved as 'ln.series' or 'ln.series.txt'."""
    for cand in (name, name + ".txt", name + ".TXT"):
        p = folder / cand
        if p.exists():
            return p
    return None


def read_bls(path: Path) -> pd.DataFrame:
    """Read a tab-delimited BLS flat file, stripping stray whitespace."""
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                     na_values=[], engine="python")
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


class LNCatalog:
    def __init__(self, folder: str):
        folder = Path(folder).expanduser()
        series_path = find_file(folder, "ln.series")
        if series_path is None:
            sys.exit(f"ERROR: could not find ln.series in {folder}\n"
                     f"Download it (and the ln.* mapping files) from "
                     f"https://download.bls.gov/pub/time.series/ln/")
        self.series = read_bls(series_path)

        # Seasonal adjustment: use column if present, else derive from ID
        if "seasonal" not in self.series.columns:
            self.series["seasonal"] = self.series["series_id"].str[2]

        # Dimension columns = every *_code column except footnotes, + seasonal
        self.dims = [c for c in self.series.columns
                     if c.endswith("_code") and c != "footnote_codes"]
        self.dims.append("seasonal")

        # Auto-discover mapping files: any ln.* file with one *_code column
        # and a matching *_text column becomes a code->label lookup.
        self.lookups = {"seasonal": {"S": "Seasonally adjusted",
                                     "U": "Not seasonally adjusted"}}
        for f in sorted(folder.iterdir()):
            name = base_name(f)
            if (not name.startswith("ln.") or name in SKIP_FILES
                    or name.startswith("ln.data")):
                continue
            try:
                t = read_bls(f)
            except Exception:
                continue
            code_cols = [c for c in t.columns if c.endswith("_code")]
            text_cols = [c for c in t.columns if c.endswith("_text")]
            if len(code_cols) == 1 and text_cols:
                self.lookups[code_cols[0]] = dict(zip(t[code_cols[0]],
                                                      t[text_cols[0]]))

        # Match each series dimension column to a lookup (exact, then prefix:
        # e.g. series column 'occ_code' <-> mapping file column
        # 'occupation_code' if BLS named them differently).
        self.dim_lookup = {}
        for d in self.dims:
            if d in self.lookups:
                self.dim_lookup[d] = self.lookups[d]
                continue
            pre = d.replace("_code", "")
            for k, v in self.lookups.items():
                kpre = k.replace("_code", "")
                if kpre.startswith(pre) or pre.startswith(kpre):
                    self.dim_lookup[d] = v
                    break

        self.max_end_year = pd.to_numeric(
            self.series.get("end_year"), errors="coerce").max()

    # ---------- helpers ----------

    def resolve_dim(self, name: str) -> str:
        """'born' -> 'born_code'; accepts exact, +_code, or unique prefix."""
        name = name.strip().lower()
        if name in self.dims:
            return name
        if name + "_code" in self.dims:
            return name + "_code"
        hits = [d for d in self.dims if d.startswith(name)]
        if len(hits) == 1:
            return hits[0]
        sys.exit(f"ERROR: unknown dimension '{name}'. "
                 f"Available: {', '.join(self.dims)}")

    def label(self, dim: str, code: str) -> str:
        return self.dim_lookup.get(dim, {}).get(code, "")

    def decorate(self, dim: str, codes: pd.Series) -> pd.Series:
        """'1' -> '1 | Men' for readable output."""
        lk = self.dim_lookup.get(dim, {})
        return codes.map(lambda c: f"{c} | {lk[c]}" if c in lk else str(c))

    def apply_filters(self, filters, title=None, active=False) -> pd.DataFrame:
        df = self.series
        for raw in filters or []:
            if "=" not in raw:
                sys.exit(f"ERROR: bad --filter '{raw}' (use dim=value)")
            key, val = raw.split("=", 1)
            dim = self.resolve_dim(key)
            val = val.strip()
            lk = self.dim_lookup.get(dim, {})
            if val in set(df[dim].unique()):
                mask = df[dim] == val                      # exact code match
            else:
                # exact label match first (so 'men' != 'Women'), then substring
                codes = [c for c, t in lk.items()
                         if val.lower() == str(t).lower()]
                if not codes:
                    codes = [c for c, t in lk.items()
                             if val.lower() in str(t).lower()]
                if not codes:
                    sys.exit(f"ERROR: '{val}' matched no code or label in "
                             f"{dim}. Try: python explore_ln.py values "
                             f"{dim.replace('_code','')}")
                mask = df[dim].isin(codes)
                matched = ", ".join(f"{c}={lk[c]}" for c in codes[:6])
                print(f"[filter] {dim}: '{val}' -> {matched}"
                      + (" ..." if len(codes) > 6 else ""))
            df = df[mask]
        if title:
            df = df[df["series_title"].str.contains(title, case=False,
                                                    regex=False)]
        if active and "end_year" in df.columns:
            df = df[pd.to_numeric(df["end_year"], errors="coerce")
                    == self.max_end_year]
        return df

    # ---------- commands ----------

    def cmd_dims(self, args):
        df = self.apply_filters(args.filter, args.title, args.active)
        print(f"\n{len(df):,} series in scope. Dimensions:\n")
        rows = []
        for d in self.dims:
            vc = df[d].value_counts()
            top = vc.index[0] if len(vc) else ""
            rows.append({
                "dimension": d.replace("_code", ""),
                "codes_used": len(vc),
                "has_lookup": "yes" if d in self.dim_lookup else "NO",
                "most_common": f"{top} | {self.label(d, top)}"[:70],
                "n_at_most_common": int(vc.iloc[0]) if len(vc) else 0,
            })
        out = pd.DataFrame(rows).sort_values("codes_used", ascending=False)
        print(out.to_string(index=False))
        print("\nTip: codes_used == 1 means that dimension never varies in "
              "this scope;\n     codes_used > 1 means you can slice by it. "
              "Drill in with `values <dim>` or `cross <dim1> <dim2>`.")

    def cmd_values(self, args):
        dim = self.resolve_dim(args.dimension)
        df = self.apply_filters(args.filter, args.title, args.active)
        vc = df[dim].value_counts().sort_index()
        print(f"\n{dim} across {len(df):,} series in scope:\n")
        out = pd.DataFrame({
            "code": vc.index,
            "label": [self.label(dim, c) for c in vc.index],
            "n_series": vc.values,
        })
        print(out.to_string(index=False))

    def cmd_profile(self, args):
        df = self.apply_filters(args.filter, args.title, args.active)
        print(f"\n{len(df):,} series match. Dimension profile:\n")
        fixed, varying = [], []
        for d in self.dims:
            vc = df[d].value_counts()
            if len(vc) <= 1:
                code = vc.index[0] if len(vc) else ""
                fixed.append((d.replace("_code", ""),
                              f"{code} | {self.label(d, code)}"))
            else:
                varying.append((d, vc))
        print("VARYING dimensions (you can slice by these):")
        for d, vc in sorted(varying, key=lambda x: -len(x[1])):
            print(f"\n  {d.replace('_code',''):<14} {len(vc)} values:")
            for code, n in vc.sort_index().items():
                print(f"      {code:>4}  {self.label(d, code):<62} "
                      f"{n:>6,} series")
        print("\nFIXED dimensions (constant in this scope):")
        for name, val in fixed:
            print(f"  {name:<14} = {val}")

    def cmd_cross(self, args):
        d1 = self.resolve_dim(args.dim1)
        d2 = self.resolve_dim(args.dim2)
        df = self.apply_filters(args.filter, args.title, args.active).copy()
        if df.empty:
            print("No series match those filters.")
            return
        df["_r"] = self.decorate(d1, df[d1])
        df["_c"] = self.decorate(d2, df[d2])
        pt = df.pivot_table(index="_r", columns="_c", values="series_id",
                            aggfunc="count", fill_value=0)
        pt.index.name = d1.replace("_code", "")
        pt.columns.name = d2.replace("_code", "")
        print(f"\nSeries counts, {len(df):,} series in scope "
              f"(0 = intersection NOT published):\n")
        print(pt.to_string())

    def cmd_find(self, args):
        df = self.apply_filters(args.filter, args.title, args.active)
        cols = ["series_id", "seasonal", "periodicity_code",
                "begin_year", "end_year", "series_title"]
        cols = [c for c in cols if c in df.columns]
        print(f"\n{len(df):,} series match"
              + (f"; showing first {args.limit}" if len(df) > args.limit
                 else "") + ":\n")
        print(df[cols].head(args.limit).to_string(index=False))

    def cmd_series(self, args):
        row = self.series[self.series["series_id"] == args.series_id.strip()]
        if row.empty:
            sys.exit(f"ERROR: {args.series_id} not found in ln.series")
        r = row.iloc[0]
        print(f"\n{r['series_id']}\n{r['series_title']}\n")
        for c in ["periodicity_code", "seasonal", "begin_year",
                  "begin_period", "end_year", "end_period"]:
            if c in row.columns:
                print(f"  {c:<18} {r[c]}")
        print("\n  Dimensions:")
        for d in self.dims:
            if d == "seasonal":
                continue
            lab = self.label(d, r[d])
            flag = "" if r[d] in ("0", "00", "000") and not lab else "  <-- "
            if lab or r[d] not in ("0", "00", "000"):
                print(f"  {flag}{d.replace('_code',''):<14} "
                      f"{r[d]:>4}  {lab}")


def main():
    p = argparse.ArgumentParser(
        description="Explore the BLS LN (CPS) series catalog.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("USAGE")[1] if "USAGE" in __doc__ else "")
    p.add_argument("-d", "--dir", default=".",
                   help="folder containing ln.series and ln.* mapping files "
                        "(default: current directory)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--filter", action="append", default=[],
                        metavar="dim=value",
                        help="repeatable; code exact or label substring")
        sp.add_argument("--title", help="series_title substring filter")
        sp.add_argument("--active", action="store_true",
                        help="only series still published (max end_year)")

    common(sub.add_parser("dims", help="overview of all dimensions"))

    sp = sub.add_parser("values", help="codes/labels used in one dimension")
    sp.add_argument("dimension")
    common(sp)

    common(sub.add_parser("profile",
                          help="which dims vary vs. are fixed, given filters"))

    sp = sub.add_parser("cross", help="series-count crosstab of two dims")
    sp.add_argument("dim1")
    sp.add_argument("dim2")
    common(sp)

    sp = sub.add_parser("find", help="list matching series IDs/titles")
    sp.add_argument("--limit", type=int, default=50)
    common(sp)

    sp = sub.add_parser("series", help="decode one series ID fully")
    sp.add_argument("series_id")

    args = p.parse_args()
    cat = LNCatalog(args.dir)
    getattr(cat, f"cmd_{args.cmd}")(args)


if __name__ == "__main__":
    main()
