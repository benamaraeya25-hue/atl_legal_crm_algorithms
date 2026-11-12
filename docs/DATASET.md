# Dataset documentation

**Name:** Supreme Court Decisions (textacy-data, `supreme_court_py3_v1.0`)
**Source file:** https://github.com/bdewilde/textacy-data/releases/download/supreme_court_py3_v1.0/supreme-court-py3.json.gz
**Contents:** 8,419 U.S. Supreme Court decisions, 1946–2016 (8,417 usable). Decision text comes from FindLaw;
metadata (date, citation, issue area, decision direction, etc.) comes from the Supreme Court Database.
**License:** metadata CC BY-NC 3.0 US (non-commercial, attribution). Not redistributed in this repo.
**Size:** ~111 MB compressed, 360,344,120 characters of text.
**Download:** `python -m caselaw.cli download` (saves to `data/raw/`).

## How the experiment corpus is built (`src/caselaw/data.py`)
1. Split each decision into sentence-like **passages** (regex split after `.`, `!`, `?` plus whitespace; keep ≥ 30 characters). Total: 2,152,182 passages.
2. Draw a seeded random sample (rate 0.6, seed 3440), shuffle, truncate to 1,000,000. Sizes 1k / 10k / 100k / 1M are prefixes, so they are nested random samples.
3. Each passage gets an integer key `date*1e9 + case_index*1e5 + sentence_index`, usable as a pinpoint citation and as a chronological sort key.

## Known limitations
- Texts and metadata were merged by a deduplication model; some mismatches are possible.
- Passage splitting is a regex and will split on abbreviations such as "U.S." or "v.".
- Only Supreme Court decisions; results about speed do not depend on content, but query hit rates do.
