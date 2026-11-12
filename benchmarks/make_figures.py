"""Build figures/*.png and results/growth_exponents.csv from the benchmark CSVs."""
import csv
import math
import os
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES, FIG = os.path.join(ROOT, "results"), os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6b6b6b"]
MARKS = ["o", "s", "^", "D", "v", "x"]
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True,
                     "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 10})


def rd(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def slope(xs, ys):
    lx, ly = [math.log(x) for x in xs], [math.log(y) for y in ys]
    mx, my = statistics.mean(lx), statistics.mean(ly)
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)


def lines(ax, series, unit):
    for i, (name, pts) in enumerate(series.items()):
        pts = sorted(pts)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker=MARKS[i % 6], color=COLORS[i % 6],
                lw=2, ms=6, label=name)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("passages (n)"); ax.set_ylabel(unit)


exps = []
# --- sorting
sr = [r for r in rd("sorting_results.csv") if r["status"] == "ok"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
for ax, scen in zip(axes, ("random", "sorted", "reversed")):
    s = defaultdict(list)
    for r in sr:
        if r["scenario"] == scen:
            s[r["algorithm"]].append((int(r["n"]), float(r["median_s"])))
    lines(ax, s, "median seconds" if scen == "random" else "")
    ax.set_title(f"Input order: {scen}")
    for name, pts in s.items():
        if len(pts) >= 3:
            exps.append(dict(task="sorting", case=scen, method=name,
                             observed_exponent=f"{slope(*zip(*[(n, max(t, 1e-9)) for n, t in pts])):.2f}",
                             points=len(pts)))
axes[0].legend(fontsize=8)
fig.suptitle("Sorting passages chronologically (log-log; missing points were skipped as quadratic)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "sorting_runtime.png"), dpi=160); plt.close(fig)

# --- comparisons
cs = rd("comparisons_sorting.csv")
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
for ax, scen in zip(axes, ("random", "reversed")):
    s = defaultdict(list)
    for r in cs:
        if r["scenario"] == scen:
            s[r["algorithm"]].append((int(r["n"]), int(r["comparisons"])))
    lines(ax, s, "key comparisons"); ax.set_title(f"Comparisons, {scen} input")
    for name, pts in s.items():
        exps.append(dict(task="comparisons", case=scen, method=name,
                         observed_exponent=f"{slope(*zip(*sorted(pts))):.2f}", points=len(pts)))
axes[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "sorting_comparisons.png"), dpi=160); plt.close(fig)

# --- lookup
lr = [r for r in rd("lookup_results.csv") if r["scenario"] in ("best", "average", "worst")]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
for ax, scen in zip(axes, ("best", "average", "worst")):
    s = defaultdict(list)
    for r in lr:
        if r["scenario"] == scen:
            s[r["method"]].append((int(r["n"]), float(r["microseconds"])))
    lines(ax, s, "microseconds per search" if scen == "best" else "")
    ax.set_title(f"{scen} case")
    for name, pts in s.items():
        exps.append(dict(task="lookup", case=scen, method=name,
                         observed_exponent=f"{slope(*zip(*sorted(pts))):.2f}", points=len(pts)))
axes[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "lookup_runtime.png"), dpi=160); plt.close(fig)

# --- retrieval: median per class at each n
rr = rd("retrieval_results.csv")
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
for ax, cls in zip(axes, ("rare", "medium", "common")):
    s = defaultdict(list)
    for n in sorted({int(r["n"]) for r in rr}):
        rows = [r for r in rr if r["query_class"] == cls and int(r["n"]) == n]
        if not rows:
            continue
        for key, label in (("naive_ms", "A scan + sort"), ("index_sort_ms", "B index + sort"),
                           ("index_heap_ms", "C index + heap Top-K")):
            s[label].append((n, statistics.median(float(r[key]) for r in rows)))
    lines(ax, s, "median ms per query" if cls == "rare" else "")
    ax.set_title(f"{cls} queries"); 
    for name, pts in s.items():
        exps.append(dict(task="retrieval", case=cls, method=name,
                         observed_exponent=f"{slope(*zip(*sorted(pts))):.2f}", points=len(pts)))
axes[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "retrieval_runtime.png"), dpi=160); plt.close(fig)

# --- selection step only, at 1M
fig, ax = plt.subplots(figsize=(7.5, 4.4))
big = [r for r in rr if int(r["n"]) == 1_000_000 and int(r["matches"]) > 1000]
big.sort(key=lambda r: int(r["matches"]))
ax.plot([int(r["matches"]) for r in big], [float(r["select_sort_ms"]) for r in big], "o-", color=COLORS[0], lw=2, label="sort all matches (merge sort)")
ax.plot([int(r["matches"]) for r in big], [float(r["select_heap_ms"]) for r in big], "s-", color=COLORS[1], lw=2, label="size-K heap (K=10)")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("matching passages (m)"); ax.set_ylabel("ms")
ax.set_title("Choosing the top 10 of m matches, n = 1,000,000"); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(FIG, "topk_selection.png"), dpi=160); plt.close(fig)

# --- memory
mem = rd("memory.csv")
fig, ax = plt.subplots(figsize=(8, 4.2))
names = [r["structure"] for r in mem]
ax.barh(names, [float(r["bytes_per_item"]) for r in mem], color=COLORS[0])
ax.set_xlabel("peak extra bytes per item"); ax.set_title("Peak extra memory (sorters: 20k items; tables: 100k)")
ax.invert_yaxis(); fig.tight_layout(); fig.savefig(os.path.join(FIG, "memory.png"), dpi=160); plt.close(fig)

with open(os.path.join(RES, "growth_exponents.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(exps[0].keys())); w.writeheader(); w.writerows(exps)
print("figures:", sorted(os.listdir(FIG)))
