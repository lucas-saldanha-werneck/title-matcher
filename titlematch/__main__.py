import argparse
import csv
import sys
from collections import Counter

from .match import Catalog, match_title


def run(catalog_path, log_path):
    cat = Catalog.from_csv(catalog_path)
    with open(log_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows, [match_title(r["raw_title"], cat) for r in rows], cat


def report(rows, results):
    naive = sum(1 for r in results if r.status == "exact")
    counts = Counter(r.status for r in results)
    n = len(results)
    out = [f"rows: {n}",
           f"exact-string match only: {naive}/{n} ({naive / n:.0%})",
           "after normalization: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))]
    if rows and "expected_id" in rows[0]:
        wrong = [(r, m) for r, m in zip(rows, results)
                 if m.status in ("exact", "normalized", "alias", "fuzzy") and m.title_id != r["expected_id"]]
        resolved = sum(1 for m in results if m.title_id)
        out.append(f"resolved: {resolved}/{n}; wrong among resolved: {len(wrong)}")
        for r, m in wrong:
            out.append(f"  WRONG {r['raw_title']!r} -> {m.title_id} (expected {r['expected_id']})")
    for m in results:
        if m.status in ("ambiguous", "unmatched"):
            out.append(f"  REVIEW {m.status}: {m.raw!r} {m.note}")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Match messy viewing-log titles to a catalog.")
    p.add_argument("catalog")
    p.add_argument("log")
    a = p.parse_args(argv)
    rows, results, _ = run(a.catalog, a.log)
    print(report(rows, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
