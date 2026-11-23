"""Normalize messy viewing-log titles so they can be compared."""
import re
import unicodedata

_TAG = re.compile(r"[\(\[](?:hd|sd|4k|uhd|dub(?:bed)?|sub(?:bed)?|live|premiere|repeat|rerun)[\)\]]", re.I)
_EPISODE = re.compile(r"\b(?:s\d{1,2}\s?e\d{1,3}|season\s\d+|episode\s\d+|ep\.?\s?\d+)\b", re.I)
_TRAILING = re.compile(r"\s+(?:repeat|rerun|hd|sd|4k)$", re.I)
_YEAR = re.compile(r"[\(\[]?\b((?:19|20)\d{2})\b[\)\]]?")
_ARTICLE = re.compile(r"^(the|a|an)\s+", re.I)


def extract_year(raw):
    m = _YEAR.search(raw)
    return int(m.group(1)) if m else None


def normalize(raw):
    s = unicodedata.normalize("NFKD", raw)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = _TAG.sub(" ", s)
    s = _TRAILING.sub("", s.strip())
    s = _EPISODE.sub(" ", s)
    s = _YEAR.sub(" ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = _ARTICLE.sub("", s)
    return s
