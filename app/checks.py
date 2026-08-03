#!/usr/bin/python
"""Self-test for the planners.

Builds small synthetic maps and checks the core invariants of each algorithm:
JPS is optimal like A*, Weighted A* stays within its bound, ARA* converges to
optimal, HPA* is feasible and never better than optimal, and unreachable goals are
rejected by everyone. Run:

    python app/checks.py
"""
import os, tempfile
import numpy as np
from PIL import Image

from util2 import Graph
from a_star import a_star, path_cost
from jps import jps
from ara_star import ara_star
from hpa_star import HPAStar

WEIGHT = 1.5


def make_map(walls, start, goal, size=20):
    # transparent-white = free, black = obstacle, green = start, red = goal
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :] = (255, 255, 255, 0)
    for (r, c) in walls:
        arr[r, c] = (0, 0, 0, 255)
    arr[start] = (0, 255, 0, 255)
    arr[goal]  = (255, 0, 0, 255)
    path = os.path.join(tempfile.gettempdir(), "perfrun_selftest.png")
    Image.fromarray(arr, "RGBA").save(path)
    return path


def check(name, condition, detail=""):
    print(f"  [{'PASS' if condition else 'FAIL'}] {name} {detail}")
    if not condition:
        raise AssertionError(name)


def raises(fn):
    try:
        fn()
        return False
    except Exception:
        return True


def open_map_invariants():
    print("open 20x20 map:")
    g = Graph(make_map([], (0, 0), (19, 19)))
    a = path_cost(a_star(g))
    w = path_cost(a_star(g, weight=WEIGHT))
    j = path_cost(jps(g))
    solutions = list(ara_star(g))
    ara_first = path_cost(solutions[0][0])
    ara_final = path_cost(solutions[-1][0])
    hpa = HPAStar(g, cluster_size=8).search()
    check("JPS optimal == A*", abs(j - a) < 1e-6, f"(jps={j:.3f} astar={a:.3f})")
    check("Weighted A* within bound", w <= a * WEIGHT + 1e-6, f"(w={w:.3f} bound={a*WEIGHT:.3f})")
    check("ARA* final == optimal", abs(ara_final - a) < 1e-6, f"(final={ara_final:.3f})")
    check("ARA* first within 2.5x", ara_first <= a * 2.5 + 1e-6, f"(first={ara_first:.3f})")
    hpa_str = f"{hpa:.3f}" if hpa is not None else "None"
    check("HPA* feasible & >= optimal", hpa is not None and hpa >= a - 1e-6, f"(hpa={hpa_str} astar={a:.3f})")


def wall_map_invariants():
    print("map with a partial wall (2-wide gap at the bottom):")
    walls = [(r, 10) for r in range(0, 18)]
    g = Graph(make_map(walls, (0, 0), (0, 19)))
    a = path_cost(a_star(g))
    j = path_cost(jps(g))
    hpa = HPAStar(g, cluster_size=8).search()
    check("JPS optimal == A* around wall", abs(j - a) < 1e-6, f"(jps={j:.3f} astar={a:.3f})")
    hpa_str = f"{hpa:.3f}" if hpa is not None else "None"
    check("HPA* feasible & >= optimal", hpa is not None and hpa >= a - 1e-6, f"(hpa={hpa_str} astar={a:.3f})")


def unreachable_invariants():
    print("unreachable goal (corner boxed in):")
    walls = [(18, 18), (18, 19), (19, 18)]
    g = Graph(make_map(walls, (0, 0), (19, 19)))
    check("A* reports no path", raises(lambda: a_star(g)))
    check("JPS reports no path", raises(lambda: jps(g)))
    check("HPA* returns None", HPAStar(g, cluster_size=8).search() is None)


def main():
    open_map_invariants()
    wall_map_invariants()
    unreachable_invariants()
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
