#!/usr/bin/python
"""Progressive A*
"""
from a_star import a_star, euclidean, H, path_cost
import time


def rasterize(p0, p1):
    # 8-connected unit-step points from p0 (exclusive) to p1 (inclusive),
    # via Bresenham's line algorithm. Every step matches a real neighbor
    # move (util2.Graph.get_neighbors only offers unit 8-connected steps),
    # so the returned chain can be validated against real graph edges.
    x0, y0 = p0
    x1, y1 = p1
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    x, y = x0, y0
    points = []
    while (x, y) != (x1, y1):
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
        points.append((x, y))

    return points


def build_dist_hint(graph, path):
    # Bootstrap the distance map for the next (finer) level from the
    # previous level's path, so a_star doesn't have to rediscover distances
    # along a corridor we already have a good estimate for.
    #
    # The chain is rasterized down to real, unit-step, walkable edges so
    # every hinted g-value stays connected back to `start` via an actual
    # path -- if the rasterized line crosses a cell that's blocked at this
    # resolution (invisible to the coarser level that produced `path`), the
    # hint simply stops there and the rest of the search proceeds normally.
    if not path:
        return None

    valid = set(graph.get_list_of_nodes())
    start = tuple(graph.get_start_node())

    hint = {}
    g    = 0.0
    pred = start
    prev = start

    waypoints = [tuple(round(c) for c in p) for p in path]

    for waypoint in waypoints:
        for node in rasterize(prev, waypoint):
            if node not in valid:
                return hint

            g += euclidean(prev, node)
            hint[node] = (g, pred)
            pred = node
            prev = node

    return hint


def pa_star(ctxt, t0, weight=1.0):
    πₗ = None

    for n in range(-1, -(len(ctxt.levels) + 1), -1):
        l_n   = ctxt.levels[n]
        graph = l_n[0]
        scale = l_n[1]

        dist_hint = build_dist_hint(graph, πₗ) if πₗ is not None else None
        π         = a_star(graph, weight, H, dist_hint)
        l_n[2]    = π

        if π is not None:
            πₗ = [(scale*v[0], scale*v[1]) for v in π] if scale != 1.0 else π

            # Capture the time to the first match
            if ctxt.firsttime is None:
                ctxt.firsttime  = time.perf_counter() - t0
                ctxt.firstcost  = path_cost(πₗ)

            # If preempted, return the last best
            if ctxt.stop:
                return πₗ

    return πₗ


class pa_ctxt:
    def __init__(self, levels):
        self.levels     = levels
        self.stop       = False
        self.firsttime  = None 
        self.firstcost  = None 
