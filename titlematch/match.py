"""Match a raw title to a catalog. Never guess when two answers are close."""
import csv
from dataclasses import dataclass
from difflib import SequenceMatcher

from .normalize import normalize, extract_year

FUZZY_MIN = 0.86   # below this: unmatched
MARGIN = 0.04      # top two different titles closer than this: ambiguous


@dataclass
class Result:
    raw: str
    status: str            # exact | normalized | alias | fuzzy | ambiguous | unmatched
    title_id: str = ""
    score: float = 0.0
    note: str = ""


class Catalog:
    def __init__(self, rows):
        # rows: dicts with id, title, year, aliases ("a|b")
        self.rows = rows
        self.raw_index = {}
        for r in rows:
            self.raw_index.setdefault(r["title"], []).append(r["id"])
        self.entries = []  # (normalized name, id, year, is_alias)
        for r in rows:
            year = int(r["year"]) if r.get("year") else None
            self.entries.append((normalize(r["title"]), r["id"], year, False))
            for a in filter(None, (r.get("aliases") or "").split("|")):
                self.entries.append((normalize(a), r["id"], year, True))

    @classmethod
    def from_csv(cls, path):
        with open(path, newline="", encoding="utf-8") as f:
            return cls(list(csv.DictReader(f)))


def _sim(a, b):
    return SequenceMatcher(None, a, b).ratio()


def match_title(raw, cat, year_hint=True):
    ids = cat.raw_index.get(raw)
    if ids and len(ids) == 1:
        return Result(raw, "exact", ids[0], 1.0)
    # a title shared by several catalog entries falls through to the year check
    norm = normalize(raw)
    year = extract_year(raw) if year_hint else None
    best = {}  # id -> (score, via_alias, exact_norm)
    for name, tid, ey, is_alias in cat.entries:
        score = 1.0 if name == norm else _sim(norm, name)
        if year and ey and year != ey:
            score -= 0.5  # the year in the log disagrees with this entry
        if tid not in best or score > best[tid][0]:
            best[tid] = (score, is_alias, name == norm)
    ranked = sorted(best.items(), key=lambda kv: -kv[1][0])
    if not ranked or ranked[0][1][0] < FUZZY_MIN:
        return Result(raw, "unmatched", score=ranked[0][1][0] if ranked else 0.0)
    top_id, (top, alias, exact_norm) = ranked[0]
    if len(ranked) > 1 and top - ranked[1][1][0] < MARGIN:
        return Result(raw, "ambiguous", score=top,
                      note=f"{top_id} vs {ranked[1][0]}: add a year or an alias")
    if exact_norm:
        return Result(raw, "alias" if alias else "normalized", top_id, top)
    return Result(raw, "fuzzy", top_id, top)
