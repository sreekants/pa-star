#!/usr/bin/python
"""Compact Hierarchical Pathfinding A* (Botea, Mueller & Schaeffer, 2004).

The grid is divided into square clusters. On every border between two adjacent
clusters we place one "transition" node per contiguous run of free cell-pairs.
Transitions inside the same cluster are linked by intra-cluster edges whose weight
is the true local A* distance; transitions facing each other across a border are
linked by an inter-cluster edge of cost 1. A query inserts the start and goal into
their own clusters and runs Dijkstra over this much smaller abstract graph.

Because the intra-cluster edge weights are real distances, the length of the
abstract path is itself a valid (slightly suboptimal) grid path length, so we
report it directly and skip reconstructing the full-resolution path.

Usage:
    solver = HPAStar(graph, cluster_size=16)   # builds the abstraction
    cost   = solver.search()                    # inserts start/goal -> length or None
"""
import heapq, math

CLUSTER = 16
INF = float("inf")


class HPAStar:
    def __init__(self, graph, cluster_size=CLUSTER):
        self.grid = graph.obstacle_map
        self.h, self.w = self.grid.shape
        self.cs = cluster_size
        self.start = tuple(graph.get_start_node())
        self.goal  = tuple(graph.get_goal_node())
        self.cluster_nodes = {}   # cluster (cr,cc) -> list of transition nodes
        self.adj = {}             # node -> list of (neighbour, cost)
        self._build()
        self._base_adj = {n: list(e) for n, e in self.adj.items()}

    # ---- helpers ----
    def _free(self, r, c):
        return 0 <= r < self.h and 0 <= c < self.w and self.grid[r][c] == 0

    def _cluster_of(self, r, c):
        return (r // self.cs, c // self.cs)

    def _add_edge(self, a, b, cost):
        self.adj.setdefault(a, []).append((b, cost))
        self.adj.setdefault(b, []).append((a, cost))

    # ---- construction ----
    def _build(self):
        ncr = (self.h + self.cs - 1) // self.cs   # number of cluster rows
        ncc = (self.w + self.cs - 1) // self.cs   # number of cluster columns

        # 1) Transitions across cluster borders (inter-cluster edges, cost 1). Each
        # border is scanned per adjacent-cluster pair (only the shared segment), so
        # every cluster that touches a free border gets its own transition node.
        for cc in range(ncc - 1):                 # vertical borders (columns c | c+1)
            c = (cc + 1) * self.cs - 1
            for cr in range(ncr):
                r0 = cr * self.cs
                self._scan_segment(lambda i: (i, c), lambda i: (i, c + 1),
                                   r0, min(r0 + self.cs, self.h))
        for cr in range(ncr - 1):                 # horizontal borders (rows r | r+1)
            r = (cr + 1) * self.cs - 1
            for cc in range(ncc):
                c0 = cc * self.cs
                self._scan_segment(lambda i: (r, i), lambda i: (r + 1, i),
                                   c0, min(c0 + self.cs, self.w))

        # 2) Intra-cluster edges between transitions of the same cluster.
        for nodes in self.cluster_nodes.values():
            unique = list(dict.fromkeys(nodes))
            for i in range(len(unique)):
                for j in range(i + 1, len(unique)):
                    d = self._local_dist(unique[i], unique[j])
                    if d is not None:
                        self._add_edge(unique[i], unique[j], d)

    def _scan_segment(self, cell_a, cell_b, lo, hi):
        # Scan one border segment [lo, hi); for each maximal run of aligned free
        # cell-pairs put a single transition at the run's midpoint.
        i = lo
        while i < hi:
            if self._free(*cell_a(i)) and self._free(*cell_b(i)):
                start = i
                while i < hi and self._free(*cell_a(i)) and self._free(*cell_b(i)):
                    i += 1
                mid = (start + i - 1) // 2
                a, b = cell_a(mid), cell_b(mid)
                self._add_edge(a, b, 1.0)
                self.cluster_nodes.setdefault(self._cluster_of(*a), []).append(a)
                self.cluster_nodes.setdefault(self._cluster_of(*b), []).append(b)
            else:
                i += 1

    def _local_dist(self, a, b):
        # 8-connected A* between a and b, confined to a's cluster.
        cr, cc = self._cluster_of(*a)
        r0, c0 = cr * self.cs, cc * self.cs
        r1, c1 = min(r0 + self.cs, self.h), min(c0 + self.cs, self.w)

        def inside(r, c):
            return r0 <= r < r1 and c0 <= c < c1 and self.grid[r][c] == 0

        open_heap = [(math.dist(a, b), 0.0, a)]
        best = {a: 0.0}
        while open_heap:
            _, g, node = heapq.heappop(open_heap)
            if node == b:
                return g
            if g > best.get(node, INF):
                continue
            r, c = node
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if not inside(nr, nc):
                        continue
                    ng = g + math.dist(node, (nr, nc))
                    if ng < best.get((nr, nc), INF):
                        best[(nr, nc)] = ng
                        heapq.heappush(open_heap, (ng + math.dist((nr, nc), b), ng, (nr, nc)))
        return None

    # ---- query ----
    def search(self):
        # Fresh copy of the abstraction, then splice in start and goal.
        self.adj = {n: list(e) for n, e in self._base_adj.items()}
        same_cluster = self._cluster_of(*self.start) == self._cluster_of(*self.goal)
        for terminal in (self.start, self.goal):
            cluster = self._cluster_of(*terminal)
            targets = list(self.cluster_nodes.get(cluster, []))
            if same_cluster:
                targets.append(self.goal if terminal == self.start else self.start)
            for t in set(targets):
                if t == terminal:
                    continue
                d = self._local_dist(terminal, t)
                if d is not None:
                    self._add_edge(terminal, t, d)
        return self._dijkstra(self.start, self.goal)

    def _dijkstra(self, source, target):
        open_heap = [(0.0, source)]
        best = {source: 0.0}
        while open_heap:
            g, node = heapq.heappop(open_heap)
            if node == target:
                return g
            if g > best.get(node, INF):
                continue
            for nb, cost in self.adj.get(node, []):
                ng = g + cost
                if ng < best.get(nb, INF):
                    best[nb] = ng
                    heapq.heappush(open_heap, (ng, nb))
        return None
