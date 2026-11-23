# titlematch

A small tool that matches messy viewing-log titles to a catalog, and refuses to guess when two catalog entries fit equally well.

Independent demo, not affiliated with Antenna.

## The problem

Viewing logs rarely carry clean titles. You see `Café Noir S01E03`, `Night Shift US S02E04`, `Quiet Feilds`, `HARBOR LIGHTS`. A catalog may hold two different titles with the same name (a series and a film, or a UK and a US version). If a pipeline matches by exact string, most rows fail. If it matches loosely, some rows get attached to the wrong title without anyone noticing.

This tool does the matching in three steps:

1. Normalize: lowercase, strip accents, drop tags like `(HD)` and `[4K]`, drop episode and season markers, drop a trailing `Repeat`, turn `&` into `and`, drop a leading article.
2. Compare against each catalog title and its aliases. A year in the log (`(2015)`) lowers the score of entries from other years.
3. Label each row `exact`, `normalized`, `alias`, `fuzzy`, `ambiguous` or `unmatched`. If the two best different titles score within 0.04 of each other, the row is `ambiguous` and gets no title id. Below 0.86 similarity, it is `unmatched`.

Standard library only (`difflib`). About 150 lines in total.

## Run it

Python 3.9+.

```sh
python -m titlematch examples/catalog.csv examples/log.csv
```

Output on the example data:

```
rows: 17
exact-string match only: 2/17 (12%)
after normalization: alias=1, ambiguous=3, exact=2, fuzzy=1, normalized=9, unmatched=1
resolved: 13/17; wrong among resolved: 0
  REVIEW ambiguous: 'Harbor Lights' c1 vs c2: add a year or an alias
  ...
```

Your own files: the catalog needs the columns `id,title,year,aliases` (aliases separated by `|`). The log needs a `raw_title` column. If the log also has an `expected_id` column, the report counts wrong matches.

## What I found while building it

The first version used a plain dictionary from title to id for exact matches. The example catalog has two entries called `Harbor Lights` (2015 and 1998). The dictionary kept the last one, so a bare `Harbor Lights` in the log was silently assigned to the 1998 film. The report showed it as one wrong match among the resolved rows. Now a title shared by several catalog entries is never resolved by exact string; it goes through the year check and ends up `ambiguous`. There is a regression test for it.

## What was tested

- 13 automated tests run offline (`pytest`, also in CI): normalization rules, year extraction, exact, alias, normalized and fuzzy matches, year disambiguation, the ambiguous case, an unknown title, the duplicate-title regression, and a full run over the example files.
- On the example files: 13 of 17 rows resolved, 0 wrong, 3 flagged ambiguous, 1 unmatched.

## What was not tested

- Real data. The catalog and the log are invented examples with made-up titles. The 12% and 76% figures say nothing about any real catalog or log.
- Scale. It compares each row against every catalog entry, so it is fine for thousands of rows and not built for millions.
- Other languages and scripts beyond accent stripping. No transliteration, no non-Latin titles.
- The thresholds (0.86 and 0.04) were picked by hand on the example data, not tuned.
- Series versus episode matching, and anything about time intervals or session attribution.
