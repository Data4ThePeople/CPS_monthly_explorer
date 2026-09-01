#!/usr/bin/env python3
"""Generate the JSON-LD for the Beyond the Unemployment Rate explorer page.

The schema is derived from the built explorer itself rather than written by
hand, so the measure list, the dimension list and the counts cannot drift away
from what the page actually offers. Re-run after build_explorer.py.

    python v2/build_schema.py            # writes v2/output/schema.jsonld

Why this shape:

  Dataset          the substance. Google Dataset Search reads variableMeasured,
                   temporalCoverage, spatialCoverage, license and creator, and
                   surfaces datasets for queries naming a measure or a
                   breakdown. The previous version named eight measures out of
                   thirty-three and none of the twenty-one breakdowns.
  WebApplication   the tool. A Dataset alone does not tell a search engine this
                   is an interactive thing you can use in a browser for free,
                   which is what someone searching "unemployment rate chart
                   tool" is looking for.
  Article          the page as editorial, carried over from the existing
                   markup so nothing already indexed is lost, with its keywords
                   widened and an `about` edge added to the Dataset.

The three nodes are cross-linked by @id, so a crawler reads them as one thing
seen three ways rather than three unrelated blobs on a page.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

V2 = Path(__file__).resolve().parent
EXPLORER = V2 / "output" / "ln_explorer.html"
OUT = V2 / "output" / "schema.jsonld"
OUT_INTRO = V2 / "output" / "schema-intro.jsonld"

PAGE = "https://www.data4thepeople.com/p/beyond-the-unemployment-rate/"
HERO = ("https://images.prismic.io/data4thepeople/"
        "1mDK_WUEazlF23Cd_cps_hero_1680x1080.jpg?auto=format,compress")
PUBLISHED = "2026-07-06T08:00:00-04:00"
MODIFIED = "2026-09-01T08:00:00-04:00"   # bump when the page changes

# The launch essay. It links to the explorer rather than redefining it: two
# Dataset nodes describing one tool would split the authority between two URLs,
# and the explorer page is the one that should rank for the tool itself.
INTRO_PAGE = "https://www.data4thepeople.com/p/cps-intro-post"
INTRO_HERO = ("https://images.prismic.io/data4thepeople/"
              "I0yRiCk2aR_rtyg6_cps_post_hero_1680x1080.jpg?auto=format,compress")
INTRO_PUBLISHED = "2026-07-07T10:00:00-04:00"
INTRO_MODIFIED = "2026-09-01T08:00:00-04:00"
REPO = "https://github.com/Data4ThePeople/CPS_monthly_explorer"
PUBLISHER = {"@type": "Organization", "name": "Data 4 The People",
             "url": "https://data4thepeople.com"}
BLS = {"@type": "Organization", "name": "U.S. Bureau of Labor Statistics",
       "url": "https://www.bls.gov"}

# Units per measure family, so each variable carries what it is counted in.
PERCENT = ("rate", "ratio", "participation")


def catalog() -> dict:
    raw = EXPLORER.read_text()
    m = re.search(r'(\{"dims".*)', raw, re.S)
    if not m:
        raise SystemExit("could not find the embedded catalog in the explorer")
    return json.JSONDecoder().raw_decode(m.group(1))[0]


def variables(cat: dict) -> list[dict]:
    """One StatisticalVariable per measure the picker offers."""
    ms = cat["measures"]
    out = []
    for code in (cat.get("measureOrder") or sorted(ms)):
        label = ms[code]
        pct = any(w in label.lower() for w in PERCENT)
        out.append({
            "@type": "StatisticalVariable",
            "name": label,
            "unitText": "percent" if pct else "persons in thousands",
            "measurementTechnique": "U.S. Census Bureau monthly household "
                                    "survey of about 60,000 addresses, "
                                    "tabulated by BLS",
            "identifier": f"BLS CPS lfst code {code}",
        })
    return out


def dimensions(cat: dict) -> list[dict]:
    """One PropertyValue per breakdown, with the groups it offers.

    This is the part search engines were missing. A query like "unemployment
    rate by veteran status" or "labor force participation by disability" only
    matches if the breakdown is named somewhere machine-readable.
    """
    out = []
    for d in cat["dims"]:
        groups = d.get("groups") or d.get("values") or []
        names = [g.get("label", g) if isinstance(g, dict) else g for g in groups]
        out.append({
            "@type": "PropertyValue",
            "name": d.get("label") or d.get("name"),
            "description": f"{len(names)} groups: " + "; ".join(str(n) for n in names),
        })
    return out


def build() -> dict:
    cat = catalog()
    vars_ = variables(cat)
    dims = dimensions(cat)
    n_series = len(cat["series"])
    n_groups = sum(len(d.get("groups") or d.get("values") or []) for d in cat["dims"])

    dim_names = [d["name"] for d in dims]
    keywords = sorted(set(
        ["Current Population Survey", "CPS data", "CPS explorer",
         "BLS data explorer", "household survey", "labor market data",
         "unemployment rate", "unemployment rate by age",
         "unemployment rate by race", "labor force participation rate",
         "employment-population ratio", "not in labor force",
         "civilian labor force", "civilian noninstitutional population",
         "labor force flows", "marginally attached workers",
         "long-term unemployment", "duration of unemployment",
         "part-time for economic reasons", "multiple jobholders",
         "employment data visualization", "free labor market tool",
         "jobs report data", "seasonally adjusted", "BLS LN database"]
        + [f"employment by {n.lower()}" for n in dim_names]))

    dataset = {
        "@type": "Dataset",
        "@id": PAGE + "#dataset",
        "name": "CPS Monthly Explorer: Published Current Population Survey "
                "Series by Dimension, Group, and Measure, 1948 to Present",
        "alternateName": ["Beyond the Unemployment Rate", "CPS Data Explorer",
                          "BLS Current Population Survey Explorer"],
        "description": (
            f"An interactive explorer over {n_series:,} published series from "
            f"the U.S. Bureau of Labor Statistics Current Population Survey "
            f"time series database (LN), covering {len(vars_)} measures across "
            f"{len(dims)} demographic and labor-market breakdowns and "
            f"{n_groups} groups, monthly from January 1948. Measures include "
            "the civilian labor force, employment, unemployment, the "
            "unemployment rate, the labor force participation rate, the "
            "employment-population ratio, the number not in the labor force, "
            "the civilian noninstitutional population, part-time and full-time "
            "employment, duration of unemployment, and the monthly labor force "
            "flows between employment, unemployment and not-in-labor-force. "
            "Breakdowns include " + ", ".join(n.lower() for n in dim_names[:-1])
            + f", and {dim_names[-1].lower()}. Every view is a single official "
            "BLS series, identified by joining the ln.series catalog to its "
            "companion code-mapping files. No values are summed, averaged "
            "across series, estimated or modeled, and the underlying BLS "
            "series ID is displayed under each chart so any figure can be "
            "verified against bls.gov."),
        "url": PAGE,
        "sameAs": REPO,
        "license": "https://www.data4thepeople.com/terms-of-use",
        "isAccessibleForFree": True,
        "temporalCoverage": "1948-01-01/..",
        "spatialCoverage": {"@type": "Place", "name": "United States"},
        "measurementTechnique": "Monthly household survey of about 60,000 "
                                "addresses (Current Population Survey), "
                                "tabulated and published by BLS",
        "creator": PUBLISHER,
        "publisher": PUBLISHER,
        "keywords": keywords,
        "variableMeasured": vars_ + dims,
        "includedInDataCatalog": {
            "@type": "DataCatalog",
            "name": "BLS Current Population Survey (LN) time series database",
            "url": "https://www.bls.gov/cps/data.htm"},
        "isBasedOn": [{
            "@type": "Dataset",
            "name": "Current Population Survey (LN) time series database",
            "description": "The U.S. Bureau of Labor Statistics publishes "
                           "monthly labor force estimates from the Current "
                           "Population Survey, a household survey of about "
                           "60,000 homes, as a public flat-file database known "
                           "as LN. Values are read as published and are not "
                           "adjusted.",
            "url": "https://www.bls.gov/cps/",
            "license": "https://www.bls.gov/bls/linksite.htm",
            "creator": BLS}],
        "citation": [
            "U.S. Bureau of Labor Statistics, Current Population Survey, "
            "https://www.bls.gov/cps/",
            "U.S. Bureau of Labor Statistics, Labor Force Statistics from the "
            "Current Population Survey (LN database), "
            "https://download.bls.gov/pub/time.series/ln/"],
    }

    app = {
        "@type": "WebApplication",
        "@id": PAGE + "#app",
        "name": "Beyond the Unemployment Rate: A CPS Data Explorer",
        "url": PAGE,
        "applicationCategory": "BusinessApplication",
        "applicationSubCategory": "Data visualization",
        "operatingSystem": "Any",
        "browserRequirements": "Requires JavaScript",
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0",
                   "priceCurrency": "USD"},
        "featureList": [
            f"Chart any of {n_series:,} published BLS Current Population "
            "Survey series",
            f"{len(vars_)} labor-market measures including the unemployment "
            "rate, labor force participation rate and employment-population "
            "ratio",
            f"{len(dims)} breakdowns and {n_groups} groups, including "
            + ", ".join(n.lower() for n in dim_names[:6]),
            "Monthly data from January 1948 to the latest BLS release",
            "Seasonal adjustment shown per series, with a twelve-month moving "
            "average drawn over not-seasonally-adjusted data",
            "The underlying BLS series ID displayed under every chart",
        ],
        "creator": PUBLISHER,
        "provider": PUBLISHER,
        "inLanguage": "en-US",
        "datePublished": PUBLISHED,
        "dateModified": MODIFIED,
        "screenshot": HERO,
        "license": "https://www.data4thepeople.com/terms-of-use",
        "audience": {"@type": "Audience",
                     "audienceType": "Journalists, researchers, policy "
                                     "analysts, students and the general "
                                     "public"},
        "about": {"@id": PAGE + "#dataset"},
        # No aggregateRating. Google lists it as an optional field for
        # SoftwareApplication and will flag its absence, but the field means
        # real user ratings; inventing one is a structured-data policy
        # violation and a manual-action risk. The warning is cosmetic, and an
        # absent rating is the correct state for a tool that collects none.
    }

    article = {
        "@type": "Article",
        "@id": PAGE + "#article",
        "headline": "Beyond the Unemployment Rate: A CPS Data Explorer",
        "description": "We built a free tool to chart 80 years of Current "
                       "Population Survey data, one official BLS series at a "
                       "time. Explore the labor market, and help us audit it.",
        "image": HERO,
        "datePublished": PUBLISHED,
        "dateModified": MODIFIED,
        "articleSection": "Visualization",
        "inLanguage": "en-US",
        "isAccessibleForFree": True,
        "keywords": keywords,
        "author": {"@type": "Person", "name": "Eric Pachman",
                   "url": "https://www.data4thepeople.com/authors/eric-pachman"},
        "publisher": PUBLISHER,
        "mainEntityOfPage": {"@type": "WebPage", "@id": PAGE},
        "about": {"@id": PAGE + "#dataset"},
        "mainEntity": {"@id": PAGE + "#app"},
    }
    return {"@context": "https://schema.org",
            "@graph": [article, dataset, app]}


def build_intro(keywords: list[str]) -> dict:
    """Schema for the launch essay.

    Carries the Article plus *stubs* of the Dataset and WebApplication defined
    on the explorer page -- @id, type, name and url, enough for a crawler to
    resolve the reference without a second full definition competing with the
    canonical one.
    """
    article = {
        "@type": "Article",
        "@id": INTRO_PAGE + "#article",
        "headline": "We Built the Labor-Market Tool That Didn't Exist",
        "description": "The unemployment rate can't see millions of people. So "
                       "we built a free tool to chart every official BLS labor "
                       "series, and we need your help auditing it.",
        "image": [INTRO_HERO],
        "datePublished": INTRO_PUBLISHED,
        "dateModified": INTRO_MODIFIED,
        "articleSection": "Labor Markets",
        "inLanguage": "en-US",
        "isAccessibleForFree": True,
        "author": {"@type": "Person", "name": "Eric Pachman",
                   "url": "https://www.data4thepeople.com/authors/eric-pachman"},
        "publisher": PUBLISHER,
        "mainEntityOfPage": {"@type": "WebPage", "@id": INTRO_PAGE},
        "keywords": keywords,
        "about": {"@id": PAGE + "#dataset"},
        "mentions": [{"@id": PAGE + "#app"}, {"@id": PAGE + "#dataset"}],
        "isBasedOn": {
            "@type": "Dataset",
            "name": "Current Population Survey (LN) time series database",
            "description": "The U.S. Bureau of Labor Statistics publishes "
                           "monthly labor force estimates from the Current "
                           "Population Survey, a household survey of about "
                           "60,000 homes, as a public flat-file database known "
                           "as LN.",
            "url": "https://www.bls.gov/cps/",
            "license": "https://www.bls.gov/bls/linksite.htm",
            "creator": BLS},
        "citation": [
            {"@type": "CreativeWork",
             "name": "Labor Force Statistics from the Current Population "
                     "Survey (LN database)",
             "url": "https://download.bls.gov/pub/time.series/ln/"},
            {"@type": "CreativeWork",
             "name": "The Employment Situation, U.S. Bureau of Labor Statistics",
             "url": "https://www.bls.gov/news.release/empsit.nr0.htm"},
            {"@type": "CreativeWork",
             "name": "Labor Force Flows, Current Population Survey",
             "url": "https://www.bls.gov/cps/cps_flows.htm"}],
    }
    # No stub nodes for the Dataset and WebApplication. Anything carrying an
    # @type is validated by Google as a real entity, so a stub with only a name
    # and url fails its type's required fields -- a Dataset wants description
    # and license, a WebApplication wants two of offers, aggregateRating,
    # applicationCategory and operatingSystem. A bare {"@id": ...} is a
    # reference rather than a definition and is not validated, while still
    # recording that this article is about the entity defined on the explorer
    # page. relatedLink gives a crawler the plain URL to follow.
    article["relatedLink"] = PAGE
    return {"@context": "https://schema.org", "@graph": [article]}


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    article, ds, app = doc["@graph"]
    print(f"wrote {OUT}")
    print(f"  Article: keywords {len(article['keywords'])}, "
          f"about -> {article['about']['@id'].rsplit('#',1)[1]}")
    print(f"  Dataset: {len(ds['variableMeasured'])} variableMeasured "
          f"({len([v for v in ds['variableMeasured'] if v['@type']=='StatisticalVariable'])} measures + "
          f"{len([v for v in ds['variableMeasured'] if v['@type']=='PropertyValue'])} breakdowns), "
          f"{len(ds['keywords'])} keywords")
    print(f"  WebApplication: {len(app['featureList'])} features")
    print(f"  {len(json.dumps(doc)):,} bytes")

    intro = build_intro(ds["keywords"] + ["labor force flows",
                                          "employed to not in labor force",
                                          "hidden unemployment",
                                          "labor market tool", "data journalism"])
    OUT_INTRO.write_text(json.dumps(intro, indent=2, ensure_ascii=False))
    print(f"\nwrote {OUT_INTRO}")
    print(f"  {len(intro['@graph'])} node(s), "
          f"{len(intro['@graph'][0]['keywords'])} keywords, "
          f"{len(json.dumps(intro)):,} bytes")
