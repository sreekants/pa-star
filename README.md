# PA* — Progressive A*

A coarse-to-fine variant of A* for grid-based path planning, developed for maritime
autonomous surface ship (MASS) navigation and submitted to *Ocean Engineering* as
"Progressive A*: An Approach to Progressive Path Planning for Maritime Autonomous
Surface Ships." This repository holds the reference implementation, benchmark suite,
test data, and the paper itself.

## What PA* does

PA* builds a pooled, multi-resolution pyramid of a grid map (in the same spirit as
CNN spatial pooling) and solves it coarsest-level-first. Each coarser solution is
rasterized into a chain of real, verified, walkable fine-grid edges, and the
accumulated cost along that chain *warm-starts* the next level's A* search — seeding
its distance map and frontier directly, before the search even begins — rather than
biasing its heuristic. Because every seeded value is a real path cost rather than an
estimate, the warm-started search is exactly as optimal as plain A* at every level:
interrupting PA* at any point still returns a complete, correct, optimal-for-its-resolution
path. See [`PAStar.md`](PAStar.md) for the full engineering writeup (algorithm,
correctness argument, complexity analysis) and [`latex/OE-V6.tex`](latex/OE-V6.tex) for
the formal paper.

## Algorithms in this repo

All under [`app/`](app/), sharing a common `Graph` abstraction over PNG occupancy maps
(`app/util2.py`, 8-connected; `app/util.py`, 4-connected, used only by Dijkstra):

| File | Algorithm |
|---|---|
| `a_star.py` | A* (optimal baseline), Weighted A*, and the `dist_hint` warm-start seeding PA* relies on |
| `pa_star.py` | **PA*** — the algorithm this project is about |
| `dijkstra.py` | Dijkstra's algorithm |
| `jps.py` | Jump Point Search |
| `ara_star.py` | Anytime Repairing A* (ARA*) |
| `hpa_star.py` | Hierarchical Path-Finding A* (HPA*) — an unrelated, pre-existing hierarchical-abstraction planner, kept as a comparison baseline |
| `pool.py` | Conservative max-pooling used to build PA*'s coarse grid levels |
| `map.py` | Benchmark harness — runs all of the above on a map and emits one CSV row |

`pa_star-old.py` is kept as a reference: an earlier corridor/heuristic-weighted design
that was replaced by the current `dist_hint` warm-start approach after it turned out to
scale poorly (see `PAStar.md` for why).

## Getting started

Requires Python 3 with `Pillow` and `numpy`.

```bash
# Self-test suite: correctness invariants for every planner
python app/checks.py

# Benchmark one category of maps, all seven planners (including PA*), CSV to stdout
python app/map.py --header
python app/map.py <outdir> samples mazes
```

PA* itself has no standalone CLI entry point — it's invoked as `pa_star(pa_ctxt(levels), t0)`
with a coarse-to-fine list of `(graph, scale)` levels; see `run_program()` in
`app/map.py` for the reference call site, or `PAStar.md` for the algorithm itself.

## Timing: overall

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

[`logs/alltests.md`](logs/alltests.md) provides a detailed analysis comparing PA* with several commonly used path planning algorithms (Dijkstra, A*, Weighted A*, ARA*, JPS).

## Benchmark data

- [`samples/`](samples/) — the test maps: eight synthetic obstacle categories (mazes,
  bugtraps, forests, gaps, and combinations; 1,000 maps each, from the SaIL/Neural A*
  benchmark set) plus real navigational charts (`samples/world/`) of the Stockholm and
  Åland archipelagos and Georgia Bay.
- [`logs/alltests.log`](logs/alltests.log) / [`alltests.s3db`](alltests.s3db) — full
  8,000-map synthetic run, as CSV and as an imported SQLite database (`app/genlogdb.py`
  does the import; `app/TransactionalDatabase.py` / `app/ActiveRecord.py` are its
  DB-access helpers). 
- [`world.csv`](world.csv) — the same run over the maritime charts.
- `map.slurm` / `map.world.slurm` / `map.trial.slurm` / `reduce.slurm` (with
  `file*.conf`) — SLURM job scripts used to run the full benchmark on NTNU's HPC cluster;
  `app/map.py` on a laptop is fine for a handful of maps, but the full 8,000-map sweep
  is a multi-hour job best run there.
- [`REPORT.md`](REPORT.md) — the analysis of that data: does PA* always find the optimal
  path, how fast, how close, compared against all six other planners.


## License

MIT — see [LICENSE](LICENSE).
