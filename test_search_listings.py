"""
Tests for search_listings() in tools.py.

Run with:  python test_search_listings.py
(plain asserts + a small runner — no pytest dependency required)

Covers the happy path plus the edge cases planned in planning.md:
  - a query that finds nothing (the required "no results" case), via three
    different routes: bad keywords, too-low price, and unmatched size
  - price filtering (inclusive boundary)
  - case-insensitive size matching ("M" matches "S/M", "M/L")
  - case-insensitive / messy descriptions and stopword-only descriptions
  - relevance ordering (best match first)
  - zero / negative price ceilings
  - that results are always real listing dicts and the function never raises
"""

from tools import search_listings


# ── tiny test runner ────────────────────────────────────────────────────────────

_PASSED = 0
_FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _PASSED, _FAILED
    if condition:
        _PASSED += 1
        print(f"  PASS  {name}")
    else:
        _FAILED += 1
        print(f"  FAIL  {name}" + (f"  — {detail}" if detail else ""))


def titles(results):
    return [r["title"] for r in results]


# ── tests ─────────────────────────────────────────────────────────────────────

def test_happy_path():
    print("\n[happy path] 'vintage graphic tee' under $30")
    results = search_listings("vintage graphic tee", max_price=30.0)
    check("returns a non-empty list", len(results) > 0, f"got {len(results)}")
    check("every result is at or below the price ceiling",
          all(r["price"] <= 30.0 for r in results))
    check("results carry the documented fields",
          all({"id", "title", "price", "platform"} <= set(r) for r in results))
    print("    ranked results:")
    for r in results:
        print(f"      ${r['price']:>5.2f}  {r['title']}")


def test_relevance_ordering():
    print("\n[ordering] graphic-tee query puts graphic/band tees on top")
    results = search_listings("faded graphic band tee", max_price=30.0)
    check("found at least 2 matches", len(results) >= 2, f"got {len(results)}")
    if results:
        top = results[0]
        tags = set(top.get("style_tags", []))
        check("top result is a graphic/band tee",
              "graphic tee" in tags or "band tee" in tags,
              f"top was {top['title']} {sorted(tags)}")


def test_no_results_bad_keywords():
    print("\n[no results] keywords that match nothing in the dataset")
    results = search_listings("scuba wetsuit snorkel flippers")
    check("returns an empty list (not an error)", results == [], f"got {titles(results)}")


def test_no_results_price_too_low():
    print("\n[no results] real keywords but an impossible price ceiling")
    results = search_listings("vintage jacket", max_price=1.0)
    check("nothing under $1 → empty list", results == [], f"got {titles(results)}")


def test_no_results_unmatched_size():
    print("\n[no results] real keywords but a size no listing has")
    results = search_listings("vintage tee", size="XXXS")
    check("no XXXS items → empty list", results == [], f"got {titles(results)}")


def test_price_boundary_inclusive():
    print("\n[price] max_price is inclusive")
    # lst_013 '90s Silk Slip Dress' is priced at exactly 30.00
    results = search_listings("90s floral slip dress", max_price=30.0)
    check("a $30.00 item is included when max_price=30.0",
          any(r["price"] == 30.0 for r in results),
          f"prices: {[r['price'] for r in results]}")


def test_size_case_insensitive():
    print("\n[size] case-insensitive token matching")
    lower = search_listings("vintage", size="m")
    upper = search_listings("vintage", size="M")
    check("'m' and 'M' return the same items", titles(lower) == titles(upper))
    check("'M' matches compound sizes like 'S/M' and 'M/L'",
          all("m" in r["size"].lower() for r in upper),
          f"sizes: {[r['size'] for r in upper]}")
    check("found at least one size-M match", len(upper) > 0)


def test_description_case_and_whitespace():
    print("\n[description] messy casing / punctuation / spacing still matches")
    a = search_listings("VINTAGE graphic TEE", max_price=30.0)
    b = search_listings("  vintage,  graphic.. tee!  ", max_price=30.0)
    check("casing doesn't change results", titles(a) == titles(search_listings("vintage graphic tee", max_price=30.0)))
    check("punctuation/extra spaces don't change results",
          titles(b) == titles(search_listings("vintage graphic tee", max_price=30.0)))


def test_stopword_only_description():
    print("\n[edge] description with only stopwords / no usable keywords")
    results = search_listings("looking for something to wear", max_price=20.0)
    check("falls back to price-filtered listings rather than empty",
          len(results) > 0 and all(r["price"] <= 20.0 for r in results),
          f"got {len(results)} results")


def test_zero_and_negative_price():
    print("\n[edge] zero and negative price ceilings")
    check("max_price=0 → empty list", search_listings("tee", max_price=0) == [])
    check("negative max_price → empty list", search_listings("tee", max_price=-5) == [])


def test_no_filters_returns_relevant_only():
    print("\n[edge] no size/price filters still drops zero-score listings")
    results = search_listings("platform sneakers")
    check("returns only keyword-relevant items", len(results) > 0)
    check("does not return the whole catalog (40 items)", len(results) < 40,
          f"got {len(results)}")


def main():
    tests = [
        test_happy_path,
        test_relevance_ordering,
        test_no_results_bad_keywords,
        test_no_results_price_too_low,
        test_no_results_unmatched_size,
        test_price_boundary_inclusive,
        test_size_case_insensitive,
        test_description_case_and_whitespace,
        test_stopword_only_description,
        test_zero_and_negative_price,
        test_no_filters_returns_relevant_only,
    ]
    for t in tests:
        t()
    print(f"\n{'=' * 50}")
    print(f"RESULTS: {_PASSED} passed, {_FAILED} failed")
    print(f"{'=' * 50}")
    return 0 if _FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
