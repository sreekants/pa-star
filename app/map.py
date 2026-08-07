#!/bin/python3

import os, sys, time
from pool import process_image
from a_star import a_star, path_cost
from pa_star import pa_star
from dijkstra import dijkstra
from ara_star import ara_star, WEIGHT_SCHEDULE
from jps import jps
from hpa_star import HPAStar, CLUSTER
from util2 import Graph

# ---- Tunable parameters -----------------------------------------------------
TILE_SIZE = 4      # coarse-grid reduction used by Progressive A* (matches pool.py)
WEIGHT    = 1.5    # heuristic inflation for Weighted A*

# ---- CSV schema -------------------------------------------------------------
# Single source of structure of the output columns. run_program builds each row in
# this exact order (guarded by an assert) and map.slurm prints the header with
# `python app/map.py --header`, so the header and the data can never drift apart
# again. Times are in seconds; *_found is 1/0; *_cost is geometric path length.
COLUMNS = [
    "category", "file",
    "density", "diffusion_mu", "diffusion_sigma", "preprocess_t",
    "dijkstra_t", "dijkstra_found", "dijkstra_cost",
    "astar_t", "astar_found", "astar_cost",
    "pastar_t", "pastar_found", "pastar_cost",
    "wastar_t", "wastar_found", "wastar_cost",
    "jps_t", "jps_found", "jps_cost",
    "ara_first_t", "ara_first_cost", "ara_final_t", "ara_final_cost", "ara_found",
    "hpa_build_t", "hpa_query_t", "hpa_found", "hpa_cost",
    "pastar_speedup",
]

def header():
    return ",".join(COLUMNS)


class Result:
    def __init__(self):
        self.density = 0.0
        self.opacity = (0.0, 0.0)
        self.preprocess_t = 0.0
        self.time  = {}   # algorithm name -> seconds
        self.found = {}   # algorithm name -> bool
        self.cost  = {}   # algorithm name -> path length (or None)
        # ARA* reports its first (fast) and final (optimal) solution separately.
        self.ara_first_t = 0.0
        self.ara_first_cost = None
        self.ara_final_t = 0.0
        self.ara_final_cost = None
        self.found["ara"] = False
        # HPA* separates the one-off abstraction build from the per-query search.
        self.hpa_build_t = 0.0
        self.hpa_query_t = 0.0
        self.found["hpa"] = False
        self.cost["hpa"] = None


def _timed(fn):
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def _fmt(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def preprocess(ret, infile, outfile):
    ret.density, ret.opacity = process_image(infile, outfile)


def build_graph(file):
    # Building the graph scans every pixel, so we do it once per map and share it
    # across planners (searches don't mutate the graph). Returns None on failure.
    try:
        t0 = time.perf_counter()
        g = Graph(file)
        return g, time.perf_counter() - t0
    except Exception:
        return None, 0


def eval_planner(ret, name, planner, graph):
    # Time a planner and record whether it found a path and the path's length.
    # `scale` rescales the reported cost (used to lift Progressive A*'s coarse-grid
    # length back to full resolution).
    found, cost = False, None
    t0 = time.perf_counter()
    if graph is not None:
        path = planner(graph)        
        if path is not None:
            found, cost = True, path_cost(path)
        else:
            found, cost = False, None
            
    ret.time[name]  = time.perf_counter() - t0
    ret.found[name] = found
    ret.cost[name]  = cost


def eval_ara(ret, graph):
    # ARA* yields improving solutions as the weight decreases to 1.0. Record the
    # first (fast, weight-suboptimal) and the last (optimal) with their arrival times.
    if graph is None:
        return
    try:
        t0 = time.perf_counter()
        first_seen = False
        final_path = None
        for path, weight in ara_star(graph, WEIGHT_SCHEDULE):
            now = time.perf_counter() - t0
            if not first_seen:
                first_seen = True
                ret.ara_first_t = now
                ret.ara_first_cost = path_cost(path)
            final_path = path
            ret.ara_final_t = now
        if final_path is not None:
            ret.found["ara"] = True
            ret.ara_final_cost = path_cost(final_path)
    except Exception:
        pass


def eval_hpa(ret, graph):
    # HPA* build (abstraction) and query (start/goal insertion + abstract search) are
    # timed separately because the abstraction is amortised over many queries.
    if graph is None:
        return
    try:
        t0 = time.perf_counter()
        solver = HPAStar(graph, CLUSTER)
        ret.hpa_build_t = time.perf_counter() - t0
        t1 = time.perf_counter()
        cost = solver.search()
        ret.hpa_query_t = time.perf_counter() - t1
        if cost is not None:
            ret.found["hpa"] = True
            ret.cost["hpa"] = cost
    except Exception:
        pass

def run_program(root, file, orig, conv):
    ret = Result()

    # Preprocess builds the coarse (pooled) map and the occupancy statistics.
    ret.preprocess_t = _timed(lambda: preprocess(ret, orig, conv))

    full, to   = build_graph(orig)   # full-resolution grid (all planners except Progressive A*)
    coarse, tc = build_graph(conv)   # pooled grid (Progressive A*)

    
    eval_planner(ret, "dijkstra", dijkstra, full)
    eval_planner(ret, "astar",    a_star,   full)
    eval_planner(ret, "pastar",   pa_star,  [(full, 1.0), (coarse, TILE_SIZE)])
    eval_planner(ret, "wastar",   lambda g: a_star(g, weight=WEIGHT), full)
    eval_planner(ret, "jps",      jps,      full)
    eval_ara(ret, full)
    eval_hpa(ret, full)

    denom   = ret.time["pastar"] +tc
    speedup = ret.time["astar"] / denom if denom > 0 else 0.0

    row = [
        root, file,
        _fmt(ret.density), _fmt(ret.opacity[0]), _fmt(ret.opacity[1]), _fmt(ret.preprocess_t),
        _fmt(ret.time["dijkstra"]), _fmt(ret.found["dijkstra"]), _fmt(ret.cost["dijkstra"]),
        _fmt(ret.time["astar"]),    _fmt(ret.found["astar"]),    _fmt(ret.cost["astar"]),
        _fmt(ret.time["pastar"]+tc),   _fmt(ret.found["pastar"]),   _fmt(ret.cost["pastar"]),
        _fmt(ret.time["wastar"]),   _fmt(ret.found["wastar"]),   _fmt(ret.cost["wastar"]),
        _fmt(ret.time["jps"]),      _fmt(ret.found["jps"]),      _fmt(ret.cost["jps"]),
        _fmt(ret.ara_first_t), _fmt(ret.ara_first_cost), _fmt(ret.ara_final_t), _fmt(ret.ara_final_cost), _fmt(ret.found["ara"]),
        _fmt(ret.hpa_build_t), _fmt(ret.hpa_query_t), _fmt(ret.found["hpa"]), _fmt(ret.cost["hpa"]),
        _fmt(speedup),
    ]
    assert len(row) == len(COLUMNS), f"row has {len(row)} fields, expected {len(COLUMNS)}"
    print(",".join(row))


def process_file(indir, outdir, category, root, file):
    if not file.endswith(".png"):
        return
    infile  = os.path.join(root, file)
    outdir  = outdir + root[len(indir):]
    outfile = os.path.join(outdir, file)
    try:
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        run_program(category, file, infile, outfile)
    except Exception:
        print(f"ERROR processing file: {infile}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--header":
        print(header())
        return
    try:
        dirpath = os.path.join(sys.argv[2], sys.argv[3])
        for root, dirs, files in os.walk(dirpath, topdown=False):
            for name in files:
                process_file(sys.argv[2], sys.argv[1], sys.argv[3], root, name)
    except Exception:
        print(f"ERROR in command: {' '.join(sys.argv)}")


if __name__ == "__main__":
    main()
