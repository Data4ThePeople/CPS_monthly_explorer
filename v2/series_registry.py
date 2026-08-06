"""Curated LN series registry and break/gap constants for the v2/ pipeline.

Single source of truth for every series ID the v2 analyses use, replacing the
per-script hardcoded dicts in scripts/. The BLS API has no catalog endpoint,
so this registry (checked against data/ln.<dimension> mapping files and the
legacy scripts) is what makes the IDs decodable.

Every charted figure remains exactly one published BLS series; the only
transforms are within-series (segments, diffs, moving averages) and each is
disclosed where used.
"""

from __future__ import annotations

import pandas as pd

# --------------------------------------------------------------------------
# Employment level by sex, 16+, in thousands

EMPLOYED_BY_SEX_SA = {
    "LNS12000000": "Both sexes",
    "LNS12000001": "Men",
    "LNS12000002": "Women",
}
EMPLOYED_BY_SEX_NSA = {
    "LNU02000000": "Both sexes",
    "LNU02000001": "Men",
    "LNU02000002": "Women",
}

# --------------------------------------------------------------------------
# Employed by industry x sex, NSA, in thousands.
# Extension point: add further confirmed (both, men, women) trios here.

INDUSTRY_GROUPS = {
    "Education and health services": {
        "both": "LNU02034574",
        "men": "LNU02037841",
        "women": "LNU02037935",
    },
}

# --------------------------------------------------------------------------
# Multiple jobholders, primary job full time / secondary part time,
# 16+, Both Sexes, NSA, thousands (mjhs code 02 per data/ln.mjhs.txt)

MULTIPLE_JOBHOLDERS_FT_PT = "LNU02026625"

# --------------------------------------------------------------------------
# Not in labor force / participation / population (nilf_charts set).
# BLS publishes NO seasonally adjusted population series (population controls
# carry no seasonal component), and no SA NILF 25-54 -- the API confirms
# LNS10000000, LNS10000060 and LNS15000060 do not exist. That nonexistent SA
# population ID is why the legacy build_nilf_charts.py never rendered chart 4.

NILF_TOTAL_SA, NILF_TOTAL_NSA = "LNS15000000", "LNU05000000"
NILF_65_NSA = "LNU05000097"          # 65+ is published NSA only
NILF_2554_NSA = "LNU05000060"        # 25-54 is published NSA only
LFPR_16_SA = "LNS11300000"
LFPR_2554_SA = "LNS11300060"
POP_16_NSA = "LNU00000000"           # population: NSA only, by construction
POP_2554_NSA = "LNU00000060"

NILF_CHART_IDS = [
    NILF_TOTAL_SA, NILF_TOTAL_NSA, NILF_65_NSA, NILF_2554_NSA,
    LFPR_16_SA, LFPR_2554_SA,
    POP_16_NSA, POP_2554_NSA,
]

# --------------------------------------------------------------------------
# Redistribution-waterfall race groups: (label, population_id, laborforce_id),
# civilian noninstitutional population vs civilian labor force, NSA.

WATERFALL_GROUPS = [
    ("White",             "LNU00000003", "LNU01000003"),
    ("Black",             "LNU00000006", "LNU01000006"),
    ("Asian",             "LNU00032183", "LNU01032183"),
    ("Two or more races", "LNU00092154", "LNU01092154"),
    ("AIAN",              "LNU00035243", "LNU01035243"),
    ("NHOPI",             "LNU00035553", "LNU01035553"),
]

# The six values as plotted in the published waterfall chart (thousands).
WATERFALL_CHART_VALUES = {
    "White": -5635,
    "Black": -631,
    "Two or more races": 3245,
    "AIAN": 1420,
    "Asian": 1068,
    "NHOPI": 393,
}

# --------------------------------------------------------------------------
# The two data hazards every analysis must respect

BREAK_MONTH = pd.Timestamp("2026-01-01")     # population-control break (footnote 12)
PRE_BREAK_END = pd.Timestamp("2025-12-01")   # last month on the old population basis
GAP_MONTH = pd.Timestamp("2025-10-01")       # never collected (footnotes 9/10/11)
BREAK_FOOTNOTE = "12"
GAP_FOOTNOTES = frozenset({"9", "10", "11"})

# BLS-published effect of the Jan-2026 population controls on the employment
# level (empsit_03062026 Table A; NSA, applied to the Dec-2025 level; thousands).
# Valid ONLY for windows that straddle the break exactly once.
POP_CTL_EFFECT_EMPLOYED_NSA = {
    "Both sexes": -1432,
    "Men": -1588,
    "Women": 155,
}

DEFAULT_BASELINE = "2023-12"


def all_series_ids() -> list[str]:
    """Every ID in the registry, deduplicated (for cache warm-up)."""
    ids = (
        list(EMPLOYED_BY_SEX_SA) + list(EMPLOYED_BY_SEX_NSA)
        + [sid for trio in INDUSTRY_GROUPS.values() for sid in trio.values()]
        + [MULTIPLE_JOBHOLDERS_FT_PT]
        + NILF_CHART_IDS
        + [sid for _, pop, lf in WATERFALL_GROUPS for sid in (pop, lf)]
    )
    return list(dict.fromkeys(ids))


def crosses_break(start, end) -> bool:
    """True if the window [start, end] spans the Jan-2026 population-control
    break, i.e. its endpoints sit on different population bases."""
    return pd.Timestamp(start) < BREAK_MONTH <= pd.Timestamp(end)


def warn_if_crosses_break(start, end, context: str) -> bool:
    if crosses_break(start, end):
        print(
            f"WARNING [{context}]: window {pd.Timestamp(start):%Y-%m} -> "
            f"{pd.Timestamp(end):%Y-%m} crosses the Jan-2026 population-control "
            "break. Levels are not comparable across it; report the segments "
            "separately instead of differencing across the seam."
        )
        return True
    return False


def noncontiguous_diff_mask(dt_index: pd.DatetimeIndex) -> pd.Series:
    """True where the previous observation is NOT the prior calendar month,
    i.e. a .diff() at that position spans a gap (e.g. Sep-2025 -> Nov-2025
    around the uncollected Oct-2025) and is not a real one-month change."""
    prev = pd.Series(dt_index, index=dt_index).shift(1)
    expected_prev = dt_index - pd.DateOffset(months=1)
    return prev.notna() & (prev != pd.Series(expected_prev, index=dt_index))


def check_break_footnote(df: pd.DataFrame) -> None:
    """Constants-drift canary: warn if the API's Jan-2026 rows do not carry
    footnote 12 (population-control revision) where we expect the break."""
    jan = df[df["date"] == BREAK_MONTH]
    if len(jan) and "footnote_codes" in jan:
        flagged = jan["footnote_codes"].str.split(",").apply(
            lambda codes: BREAK_FOOTNOTE in codes
        )
        if not flagged.all():
            missing = jan.loc[~flagged, "series_id"].unique()
            print(
                "NOTE: Jan-2026 rows without footnote 12 (population-control "
                "revision) for: " + ", ".join(missing) + " -- verify that "
                "BREAK_MONTH in series_registry.py is still correct."
            )


if __name__ == "__main__":
    ids = all_series_ids()
    print(f"{len(ids)} unique series in the registry:")
    for sid in ids:
        print(f"  {sid}")
