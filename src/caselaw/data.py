"""Loading and preparing the U.S. Supreme Court decisions dataset.

Dataset: "Supreme Court Decisions" from the textacy-data project
    https://github.com/bdewilde/textacy-data/releases/tag/supreme_court_py3_v1.0
    8,419 decisions, November 1946 to June 2016. Decision text comes from FindLaw;
    metadata comes from the Supreme Court Database (CC BY-NC 3.0 US).

The raw file (about 111 MB compressed) is NOT stored in the repository. Run
    python -m caselaw.cli download
to fetch it into data/raw/.

A "passage" is one sentence-like piece of a decision. Passages are the items the
experiments scale over (1,000 up to 1,000,000 passages).
"""
from __future__ import annotations

import gzip
import json
import os
import pickle
import random
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_URL = ("https://github.com/bdewilde/textacy-data/releases/download/"
            "supreme_court_py3_v1.0/supreme-court-py3.json.gz")
DEFAULT_RAW = ROOT / "data" / "raw" / "supreme-court-py3.json.gz"
CACHE_DIR = ROOT / "data" / "processed"

MIN_PASSAGE_CHARS = 30      # shorter pieces are headings, citations or fragments
MAX_CASES = 10 ** 4         # key packing reserves 4 digits for the case number
MAX_SENT = 10 ** 5          # and 5 digits for the passage number inside a case
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def raw_path() -> Path:
    """Location of the raw dataset (override with the SCOTUS_DATA environment variable)."""
    return Path(os.environ.get("SCOTUS_DATA", DEFAULT_RAW))


def download(dest: str | Path | None = None) -> Path:
    """Download the raw dataset if it is not already on disk."""
    dest = Path(dest) if dest else raw_path()
    if dest.exists():
        print(f"already present: {dest}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)

    def hook(blocks, block_size, total):
        if total > 0:
            done = min(blocks * block_size, total)
            sys.stdout.write(f"\rdownloading {done / 1e6:6.1f} / {total / 1e6:.1f} MB")
            sys.stdout.flush()

    urllib.request.urlretrieve(DATA_URL, dest, reporthook=hook)
    print(f"\nsaved to {dest}")
    return dest


def iter_cases(path: str | Path | None = None):
    """Yield one dict per decision. Decisions with no text or no date are skipped."""
    path = Path(path) if path else raw_path()
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("text") and rec.get("decision_date"):
                yield rec


def split_passages(text: str) -> list[str]:
    """Split a decision into sentence-like passages (split after . ! ? plus whitespace).

    This is deliberately simple. It also splits after abbreviations such as "v." and
    "U.S.", which makes some passages short; passages under MIN_PASSAGE_CHARS are dropped.
    """
    return [p for p in (s.strip() for s in _SENT_SPLIT.split(text)) if len(p) >= MIN_PASSAGE_CHARS]


def pack_key(date: str, case_idx: int, sent_idx: int) -> int:
    """Pack (decision date, case number, passage number) into one sortable integer.

    Sorting these keys orders passages by decision date, then case, then position in the
    decision. It doubles as a 'pinpoint citation' that identifies one passage uniquely.
    """
    return int(date.replace("-", "")) * 10 ** 9 + case_idx * 10 ** 5 + sent_idx


def unpack_key(key: int) -> tuple[int, int, int]:
    date, rest = divmod(key, 10 ** 9)
    case_idx, sent_idx = divmod(rest, 10 ** 5)
    return date, case_idx, sent_idx


@dataclass
class Corpus:
    texts: list[str]
    lowered: list[str]
    keys: list[int]
    cases: list[dict]
    stats: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.texts)

    def subset(self, n: int) -> "Corpus":
        """The first n passages. Passages are stored in a fixed random order, so every
        subset is a random sample and smaller subsets are contained in larger ones."""
        return Corpus(self.texts[:n], self.lowered[:n], self.keys[:n], self.cases, self.stats)


def build_corpus(path: str | Path | None = None, sample_rate: float = 0.6, seed: int = 3440,
                 max_passages: int = 1_000_000, progress: bool = True) -> Corpus:
    """Read the dataset once, keep each passage with probability sample_rate, shuffle the
    kept passages with a fixed seed, and keep the first max_passages of them."""
    rng = random.Random(seed)
    texts: list[str] = []
    keys: list[int] = []
    cases: list[dict] = []
    total_passages = total_chars = 0
    for rec in iter_cases(path):
        ci = len(cases)
        if ci >= MAX_CASES:
            raise ValueError("more than 10,000 cases: widen the key packing in pack_key")
        cases.append({"name": rec.get("case_name") or "", "date": rec["decision_date"],
                      "cite": rec.get("us_cite_id") or ""})
        passages = split_passages(rec["text"])
        total_passages += len(passages)
        total_chars += len(rec["text"])
        for si, p in enumerate(passages[:MAX_SENT]):
            if rng.random() < sample_rate:
                texts.append(p)
                keys.append(pack_key(rec["decision_date"], ci, si))
        if progress and ci % 1000 == 999:
            print(f"  read {ci + 1} decisions, kept {len(texts):,} passages", flush=True)
    order = list(range(len(texts)))
    rng.shuffle(order)
    order = order[:max_passages]
    if len(order) < max_passages:
        print(f"warning: only {len(order):,} passages available; raise sample_rate", file=sys.stderr)
    texts = [texts[i] for i in order]
    keys = [keys[i] for i in order]
    lowered = [t.lower() for t in texts]
    stats = {"cases": len(cases), "passages_total": total_passages, "chars_total": total_chars,
             "passages_kept": len(texts), "sample_rate": sample_rate, "seed": seed}
    return Corpus(texts, lowered, keys, cases, stats)


def cache_path(max_passages: int = 1_000_000, sample_rate: float = 0.6, seed: int = 3440) -> Path:
    return CACHE_DIR / f"corpus_{max_passages}_{sample_rate}_{seed}.pkl"


def load_or_build(max_passages: int = 1_000_000, sample_rate: float = 0.6, seed: int = 3440,
                  path: str | Path | None = None) -> Corpus:
    """Return the corpus, using a pickle cache in data/processed/ (not committed)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = cache_path(max_passages, sample_rate, seed)
    if cache.exists():
        with open(cache, "rb") as f:
            return pickle.load(f)
    corpus = build_corpus(path, sample_rate, seed, max_passages)
    with open(cache, "wb") as f:
        pickle.dump(corpus, f, protocol=pickle.HIGHEST_PROTOCOL)
    return corpus
