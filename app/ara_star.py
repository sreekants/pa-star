#!/usr/bin/python
"""Anytime Repairing A* (Likhachev et al., 2003) - simple, readable variant.

ARA* returns a fast, bounded-suboptimal path quickly and then improves it toward
optimal as more time becomes available. This version re-runs the shared Weighted
A* at a decreasing sequence of heuristic weights and yields each improving
solution, best (optimal) last.

It favours readability over the original's incremental OPEN/INCONS reuse, so later
iterations recompute from scratch. The *sequence of solutions* it produces is the
same; only the cumulative time to reach the optimal one is higher than a true
incremental ARA* would be. Callers therefore usually report the first (fast)
solution as ARA*'s headline result and the last as its converged optimum.
"""
from a_star import a_star

WEIGHT_SCHEDULE = [2.5, 2.0, 1.5, 1.0]


def ara_star(graph, schedule=WEIGHT_SCHEDULE):
    # Yield (path, weight) for each weight, ending at the optimal (weight 1.0) path.
    for weight in schedule:
        yield a_star(graph, weight=weight), weight
