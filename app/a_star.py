#!/usr/bin/python

from util2 import Graph
import heapq, sys, math


# You should only need to use the following functions to implement A*:
# Graph(path_to_map) # path_to_map can, for instance, be 'maps/map1.png'
# graph.get_list_of_nodes()
# graph.get_neighbors(node)
# graph.get_start_node()
# graph.get_goal_node()

# For visualizing the algorithm use the following functions:
# graph.add_visited_node(node) # Use this when you are visiting a new node to update the visualization
# graph.add_shortest_path(path) # Use this to visualize the shortest path after you have found it.

def euclidean(start, end):
    return math.sqrt( (start[0]-end[0])**2+ (start[1]-end[1])**2 )

def manhattan(start, end):
    return abs(start[0]-end[0])+ abs(start[1]-end[1])

def H(graph, n, goal):
    # distance to the end goal.
    return euclidean( n, goal )

def D(graph, start, end):
    return euclidean(start, end)

def a_star(graph:Graph, weight=1.0, heuristic_function=None, dist_hint=None):
    # A* search. With weight=1.0 this is standard (optimal) A*; with weight>1.0 it
    # becomes Weighted A*, which is faster but only guarantees a path within
    # `weight` times the optimal cost. Returns the path from start to goal as a
    # sequential list of nodes.
    #
    # dist_hint, if given, is a {node: (g, predecessor)} map used to bootstrap
    # `dist` and seed the frontier -- e.g. from a coarser level's solution --
    # so the search doesn't have to rediscover distances along a corridor we
    # already have a good estimate for. Every entry must already be a real,
    # connected, admissible (g, predecessor) pair reachable from `start`.

    start = tuple(graph.get_start_node())
    dest = tuple(graph.get_goal_node())
    heuristic = H if heuristic_function is None else heuristic_function

    vertices = graph.get_list_of_nodes()

    # initialize distance maps
    dist = {v: (float('infinity'),None) for v in vertices}
    dist[start] = (0, None)

    # Track a priority queue to pick the shortest next step. Entries carry the g
    # they were pushed with, so stale ones (superseded by a cheaper path) can be
    # recognised and skipped when popped.
    frontier = [(0, 0, start)]

    if dist_hint:
        for node, (g, pred) in dist_hint.items():
            if node == start:
                continue
            dist[node] = (g, pred)
            h = heuristic(graph, node, dest)
            heapq.heappush(frontier, (g + weight*h, g, node))

    current = start
    graph.add_visited_node(start)

    while len(frontier):
        currf, currg, current = heapq.heappop(frontier)

        if current == dest:
            break

        # Skip stale entries: a cheaper path to this node was pushed later.
        if currg > dist[current][0]:
            continue

        currdist    = currg
        neighbours  = graph.get_neighbors(current)
        for next in neighbours:
            graph.add_visited_node(next)
            g       = currdist + D(graph, current, next)

            if g < dist[next][0]:

                dist[next] = (g,current)

                h       = heuristic(graph, next, dest)
                f       = g + weight*h

                heapq.heappush( frontier, (f, g, next) )

                #print( f'({current[1]},{4-current[0]}) ({next[1]},{4-next[0]}) : F={f:.1f} G={g:.1f} H={h:.1f}' )


    # No path exists if the goal was never relaxed off infinity.
    if dist[dest][0] == float('infinity'):
        return None

    # Build the path from goal back to start (following predecessors to the
    # start, whose predecessor is None), then reverse to start..goal order.
    path = []
    current = dest
    while current is not None:
        path.append(current)
        current = dist[current][1]
    path.reverse()

    return path


def path_cost(path):
    # Geometric (Euclidean) length of a path given as a list of (i,j) nodes.
    return sum(euclidean(path[i], path[i+1]) for i in range(len(path) - 1))

if __name__ == "__main__":
    graph = Graph(sys.argv[1])
    path = a_star(graph, heuristic_function=None)

    print(path)
