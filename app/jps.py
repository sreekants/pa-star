#!/usr/bin/python
"""Jump Point Search (Harabor & Grastien, 2011) on a uniform-cost 8-connected grid.

JPS returns optimal grid paths like A* but expands far fewer nodes: instead of
pushing every cell onto the open list it "jumps" along a direction, skipping
uniform stretches until it reaches a decision point (a jump point). Only jump
points are queued, which is what makes it fast.

Movement model: standard no-corner-cutting - a diagonal step is blocked only when
both of its adjacent orthogonal cells are obstacles. util2.Graph's A* is slightly
more permissive (it will squeeze through a diagonal gap), so on rare maze-like maps
jps() may report a marginally longer path than a_star(); everywhere else they agree
exactly.

For readability this implementation expands all eight directions from every node
instead of pruning by travel direction. Optimality is unaffected - it just performs
a few redundant jumps - and it keeps the core speed benefit (only jump points are
queued).

Interface matches the other planners: jps(graph) -> list of nodes (start..goal).
"""
import heapq, math

_DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
               ( 0, -1),          ( 0, 1),
               ( 1, -1), ( 1, 0), ( 1, 1)]


def _walkable(grid, r, c):
    return 0 <= r < grid.shape[0] and 0 <= c < grid.shape[1] and grid[r][c] == 0


def _jump(grid, r, c, dr, dc, goal):
    # Step from (r,c) along (dr,dc) until we hit a jump point, the goal or a wall.
    # Returns the jump point (r,c) or None. Iterative along the travel direction so
    # long straight runs cannot overflow the recursion limit.
    while True:
        nr, nc = r + dr, c + dc
        if not _walkable(grid, nr, nc):
            return None
        if dr != 0 and dc != 0 and not (_walkable(grid, nr, c) or _walkable(grid, r, nc)):
            return None                      # no corner cutting through a diagonal gap
        r, c = nr, nc
        if (r, c) == goal:
            return (r, c)

        if dr != 0 and dc != 0:
            # Diagonal: a jump point if a nearby obstacle forces a neighbour...
            if (_walkable(grid, r - dr, c + dc) and not _walkable(grid, r - dr, c)) or \
               (_walkable(grid, r + dr, c - dc) and not _walkable(grid, r, c - dc)):
                return (r, c)
            # ...or if either straight component finds one (one level of recursion;
            # those calls loop iteratively, so total depth stays tiny).
            if _jump(grid, r, c, dr, 0, goal) is not None or \
               _jump(grid, r, c, 0, dc, goal) is not None:
                return (r, c)
        elif dr != 0:                        # vertical move
            if (_walkable(grid, r + dr, c + 1) and not _walkable(grid, r, c + 1)) or \
               (_walkable(grid, r + dr, c - 1) and not _walkable(grid, r, c - 1)):
                return (r, c)
        else:                                # horizontal move
            if (_walkable(grid, r + 1, c + dc) and not _walkable(grid, r + 1, c)) or \
               (_walkable(grid, r - 1, c + dc) and not _walkable(grid, r - 1, c)):
                return (r, c)
        # no jump point yet: keep moving in the same direction (loop)


def jps(graph):
    grid  = graph.obstacle_map
    start = tuple(graph.get_start_node())
    goal  = tuple(graph.get_goal_node())

    dist   = {start: 0.0}
    parent = {start: None}
    open_heap = [(math.dist(start, goal), start)]

    while open_heap:
        _, node = heapq.heappop(open_heap)
        if node == goal:
            break
        r, c = node
        for dr, dc in _DIRECTIONS:
            jp = _jump(grid, r, c, dr, dc, goal)
            if jp is None:
                continue
            g = dist[node] + math.dist(node, jp)
            if jp not in dist or g < dist[jp]:
                dist[jp]   = g
                parent[jp] = node
                heapq.heappush(open_heap, (g + math.dist(jp, goal), jp))

    if goal not in parent:
        return None

    # Reconstruct from jump points; each segment between them is a straight or
    # diagonal line, so the node list captures the full geometric length.
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path
