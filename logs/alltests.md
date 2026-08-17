# Benchmark Analysis: `logs/alltests.s3db`

Analysis of the `samples` table in `logs/alltests.s3db` — 8,000 procedurally generated
201x201 grid maps, 1,000 each across 8 categories (`mazes`, `bugtrap_forest`, `forest`,
`gaps_and_forest`, `alternating_gaps`, `shifting_gaps`, `single_bugtrap`,
`multiple_bugtraps`), each run through seven planners: Dijkstra, A\* (optimal baseline,
`weight=1.0`), PA\* (`pastar`, two-level coarse-to-fine warm start), Weighted A\*
(`wastar`, `weight=1.5`), JPS, ARA\* (anytime, schedule down to `weight=1.0`), and
hierarchical HPA\* (`cluster_size=16`). All numbers below are computed directly against
the 8,000 rows in this database; every figure is a real aggregate, not an estimate.

---

## 1. Dataset overview

| | |
|---|---:|
| Total maps | 8,000 |
| Maps per category | 1,000 |
| Maps where A\* found no path (genuinely unreachable goal) | 103 (all in `gaps_and_forest`) |
| Maps where A\* found a path | 7,897 |

`gaps_and_forest` is the densest category by a wide margin (mean obstacle density 0.356
vs. 0.06-0.18 for the others) and is the *only* category containing unsolvable instances
— all 103 unreachable maps in the dataset come from it.

Every planner except JPS agrees exactly with A\* on which 103 maps are unreachable:

| Algorithm | Disagrees with `astar_found` |
|---|---:|
| Dijkstra | 0 / 8,000 |
| PA\* | 0 / 8,000 |
| Weighted A\* | 0 / 8,000 |
| ARA\* | 0 / 8,000 |
| HPA\* | 0 / 8,000 |
| JPS | **1 / 8,000** (missed a map A\* solved — `gaps_and_forest`, id 7220) |

---

## 2. Solution quality vs. the A\* optimum

Restricted to the 7,897 maps A\* solved, comparing each planner's reported cost to
`astar_cost` (`path_cost()` in every planner is a true Euclidean-length metric, so costs
are directly comparable):

| Algorithm | Exact match | Worse than A\* | Better than A\* | Mean overcost | Max overcost |
|---|---:|---:|---:|---:|---:|
| **PA\*** | **7,897 / 7,897 (100%)** | 0 | 0 | 0.000% | 0.000% |
| ARA\* (final) | 7,897 / 7,897 (100%) | 0 | 0 | 0.000% | 0.000% |
| JPS | 7,893 / 7,896 (99.96%) | 3 | 0 | 0.001% | 2.44% |
| Weighted A\* (w=1.5) | 6,364 / 7,897 (80.6%) | 1,533 | 0 | 0.259% | 11.11% |
| Dijkstra | 3,702 / 7,897 (46.9%) | 4,195 | 0 | 1.987% | 24.21% |
| HPA\* | 0 / 7,897 (0%) | 7,897 | 0 | 2.224% | 8.55% |

**PA\* never returns a suboptimal or wrong path.** Its cost matches `astar_cost` to
floating-point exactness on every one of the 7,897 comparable maps — consistent with the
`dist_hint` warm-start design being a strict re-ordering of A\*'s own search, not an
approximation (see `PAStar.md` §4 for the correctness argument this empirically
confirms at full dataset scale, not just the 24-map sample it was originally checked
against).

**Weighted A\* respects its theoretical bound with zero violations**: no row exceeds
`1.5 x astar_cost`, even though 1,533 rows (19.4%) are measurably worse than optimal —
exactly the trade the weight parameter promises.

**HPA\* is worse on literally every solvable map** (7,897/7,897), by a mean of 2.22% and
up to 8.55%. This is structural, not a bug: HPA\* searches an abstracted cluster graph
and is only feasible/bounded, never cost-optimal.

**Dijkstra's cost figures should not be read as a fair baseline in this run.** Dijkstra
disagrees with A\* on 4,195 of 7,897 maps (53.1%), by up to 24% — despite both algorithms
supposedly finding the shortest path on the same graph. `app/dijkstra.py` was patched in
a later commit (`895e406`, "Fix Dijkstra bugs to use Euclidean distance like other
baselines") to address exactly this class of issue, but **this benchmark run predates
that fix**: `logs/alltests.log` is dated before the fix commit, and `logs/alltests.s3db`
was rebuilt from that same unmodified log afterward (a re-import, not a re-run). The
numbers above reflect the pre-fix Dijkstra implementation — they say nothing about
Dijkstra's current correctness, only about the run that produced this dataset.

**JPS's 3 mismatches and 1 missed path** are small (largest overcost +2.44%, 0.04% of
maps affected) and plausibly a jump-point-pruning edge case in a specific obstacle
configuration rather than a systemic issue, given `jps.py` already uses correct
pop-based goal termination.

---

## 3. Timing: overall

Mean / median wall-clock time in seconds, across all rows where the algorithm ran
(`n=8000` for the primary time column, `n=7897` for `first_time`, which is only
meaningful when a path was found):

| Algorithm | Mean | Median |
|---|---:|---:|
| HPA\* (build + query) | **0.090** | 0.085 |
| **PA\* first/anytime result** | **0.046** | **0.029** |
| Weighted A\* | 0.326 | 0.084 |
| Dijkstra | 0.423 | 0.425 |
| A\* | 0.498 | 0.523 |
| PA\* (final, refined) | 0.565 | 0.592 |
| ARA\* (first solution) | 1.068 | 0.244 |
| JPS | 1.314 | 0.289 |
| ARA\* (final, w->1.0) | 2.483 | 0.990 |

Two things stand out immediately:

- **PA\*'s final, fully-refined result is never faster than plain A\*.** Restricted to
  the 7,897 jointly-solved maps, `pastar_t < astar_t` on **0 rows** — zero exceptions.
  Mean ratio `pastar_t / astar_t` = **1.19x** (median 1.13x, worst case 5.28x). This
  matches the design: PA\* runs a coarse search *and* a fine search plus hint
  construction, which is structurally more work than a single A\* pass.
- **PA\*'s anytime "first" result — the coarse-level solution available the moment the
  first pyramid level finishes, well before the fine-resolution refinement even starts —
  is dramatically faster**: mean **17.8x** faster than a full A\* search (median 18.5x,
  worst case still 0.87x — comparable, never catastrophic). It beats `astar_t` outright
  on 7,648 / 7,897 maps (96.8%). Its cost is close to optimal even before refinement:
  mean 1.2% overcost, exactly optimal already on 13.5% of maps, worst case 30.8% over.
  (The database's own `first_speedup` column reports a lower mean, ~7.9x, using a
  derivation not reproducible from the code currently checked in; the 17.8x figure above
  is self-computed as `astar_t / first_time` directly from the raw timing columns.)

This is PA\*'s actual value proposition in this codebase: not beating A\* on the final
answer, but making a usable, near-optimal, complete path available roughly an order of
magnitude sooner for a caller that can't wait for the fully-refined result — the
anytime/interruptible use case, not a drop-in "faster A\*."

A minor, expected wrinkle: in 692 of 7,897 rows (8.8%) `first_cost` comes in *below*
`astar_cost` (never by more than 0.62%, mean undershoot 0.32%). This isn't a broken
optimality guarantee — `first_cost` scores the coarse path's own rescaled polyline
waypoints, not a rasterized fine-grid path, so it can occasionally cut a corner the
finer lattice's forced unit steps can't, purely as a discretization artifact.

---

## 4. Category-level behavior

Mean values per category (only rows where A\* found a path):

| Category | Density | A\* t | PA\* t | PA\*/A\* ratio | W-A\* t | JPS t | ARA\* final t | HPA\* t | PA\* first t | First speedup |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_bugtrap | 0.057 | 0.392 | 0.449 | **1.49x** | 0.074 | 0.180 | 0.760 | 0.068 | 0.022 | 16.4x |
| multiple_bugtraps | 0.075 | 0.546 | 0.613 | 1.13x | 0.363 | 0.403 | 2.333 | 0.117 | 0.041 | 17.4x |
| mazes | 0.076 | 0.329 | 0.381 | 1.21x | 0.315 | 0.094 | 1.480 | 0.139 | 0.017 | 19.0x |
| bugtrap_forest | 0.153 | 0.673 | 0.753 | 1.12x | 0.293 | 3.056 | 2.139 | 0.102 | 0.036 | 19.2x |
| forest | 0.165 | 0.478 | 0.549 | 1.16x | 0.032 | 1.807 | 0.575 | 0.097 | 0.027 | 18.4x |
| alternating_gaps | 0.185 | 0.610 | 0.688 | 1.13x | 0.178 | 0.288 | 2.362 | 0.074 | 0.033 | 18.5x |
| shifting_gaps | 0.185 | 0.366 | 0.420 | 1.16x | 0.065 | 0.191 | 0.914 | 0.052 | 0.020 | 18.6x |
| gaps_and_forest | 0.355 | 0.613 | 0.686 | 1.12x | 1.321 | 4.597 | 10.371 | 0.077 | 0.186 | 14.6x |

Notable, category-specific patterns:

- **The PA\*/A\* time-ratio penalty is worst on the easiest category, not the hardest.**
  `single_bugtrap` (lowest density, 0.057) has by far the largest mean ratio (1.49x,
  worst-case 5.28x), while every other category clusters tightly around 1.12x-1.21x.
  Within `single_bugtrap`, `astar_t` is bimodal — many maps solve in ~0.01s, others in
  ~0.45-0.85s — and there's a strong negative correlation (Pearson **-0.67**) between
  `astar_t` and the PA\*/A\* ratio: when the underlying search is already trivially fast,
  PA\*'s roughly-fixed per-query overhead (loading the coarse graph, rasterizing and
  seeding the hint, running a second search) stops being amortized and dominates the
  ratio instead. This is a fixed-cost-vs-small-baseline effect, not evidence PA\* scales
  worse on easy maps in absolute terms.

- **Weighted A\* is *slower* than plain A\* on every single map in `gaps_and_forest`**
  (897/897, mean 0.48x "speedup" — i.e., ~2.1x slower), the exact opposite of its
  behavior everywhere else (6.5x-21x faster on the other seven categories). This
  category is also the densest (0.355) and the only one with unreachable goals. A
  higher, non-admissible-in-the-traditional-sense weight pushes the search more
  aggressively toward the goal, which pays off in open space but appears to cause
  excess re-expansion/backtracking once the map is dense enough that the greedy
  push repeatedly runs into dead ends — worth a closer look if Weighted A\*'s
  behavior on dense maps becomes a focus, since it's a clean, reproducible reversal
  rather than noise (it holds on every one of the 897 rows).

- **JPS's advantage depends heavily on obstacle structure.** It's 2-3.4x faster than A\*
  in `mazes`, `alternating_gaps`, `shifting_gaps`, and `single_bugtrap` (corridor-like,
  jump-friendly structure), but 0.2x-0.4x the speed of A\* (i.e., 3-5x *slower*) in
  `bugtrap_forest`, `forest`, and `gaps_and_forest` — the categories with scattered
  small obstacles, where jump-point pruning has little open space to skip over and its
  bookkeeping overhead dominates instead.

- **HPA\*'s overcost tracks density.** Mean overcost ranges from 1.7% (`alternating_gaps`,
  density 0.185) up to 3.3% (`gaps_and_forest`, density 0.355, worst single-map 8.5%) —
  denser obstacle fields make the cluster-graph abstraction's shortcuts less accurate
  relative to the true optimum.

- **ARA\*'s final-solution time is the most density-sensitive of any planner**: 0.575s
  mean in `forest` (density 0.165) vs. 10.37s mean in `gaps_and_forest` (density 0.355,
  the map family with the largest gap between ARA\* and every other planner in the
  table) — its repeated re-solves under a shrinking weight schedule compound with map
  difficulty faster than a single-pass search does.

---

## 5. Bottom line

| Algorithm | Mean time | Median time | Cost vs. A\* optimal |
|---|---:|---:|---|
| **PA\* (first/anytime)** | **0.046 s** | **0.029 s** | 1.2% overcost on average, exact 13.5% of the time |
| HPA\* | 0.090 s | 0.085 s | worse on 100% of maps, mean +2.2%, max +8.5% |
| Weighted A\* (w=1.5) | 0.326 s | 0.084 s | worse on 19.4%, always within the 1.5x bound |
| Dijkstra* | 0.423 s | 0.425 s | worse on 53.1% (*pre-fix run, see §2) |
| A\* | 0.498 s | 0.523 s | optimal by definition |
| **PA\* (final)** | 0.565 s | 0.592 s | **exact match, 100%** |
| ARA\* (first) | 1.068 s | 0.244 s | — |
| JPS | 1.314 s | 0.289 s | worse on 0.04% (3 maps), missed 1 solvable map |
| ARA\* (final) | 2.483 s | 0.990 s | exact match, 100% (by design) |

Across all 8,000 maps: **PA\* never returns a wrong or suboptimal final path, and never
disagrees with A\* about path existence.** Its fully-refined result is consistently —
not occasionally — a little slower than a single A\* pass (mean 1.19x, never faster,
worst case 5.28x, with the worst ratios concentrated on the easiest/sparsest maps where
fixed per-query overhead isn't amortized). Its practical payoff is the anytime behavior:
a complete, connected, typically near-optimal path (1.2% overcost on average, exact
13.5% of the time) is available ~17.8x faster than waiting for full A\*, which is the
relevant comparison for a planner that needs to act before the fully-refined result is
ready, rather than a claim that PA\* is a faster drop-in replacement for A\*.

Among the non-PA\* baselines: HPA\* is the fastest "real" (non-preview) result but never
optimal; Weighted A\* offers a tunable, boundedly-suboptimal middle ground that is
mostly (but not universally — see `gaps_and_forest` above) faster than A\*; JPS's
performance is highly structure-dependent, helping a lot on open/corridor maps and
hurting on cluttered ones; ARA\* is the slowest planner here by a wide margin but
converges to the exact optimum by construction, same as PA\*'s final result.
