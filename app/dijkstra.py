#!/usr/bin/python
from util import Graph
import heapq, sys, math

# You should only need to use the following functions to implement dijkstra:
# Graph(path_to_map) # path_to_map can, for instance, be 'maps/map1.png'
# graph.get_list_of_nodes()
# graph.get_neighbors(node)
# graph.get_start_node()
# graph.get_goal_node()

# For visualizing the algorithm use the following functions:
# graph.add_visited_node(node) # Use this when you are visiting a new node to update the visualization
# graph.add_shortest_path(path) # Use this to visualize the shortest path after you have found it.

def g(graph, start, end):
    # Euclidean step cost between adjacent cells: 1 for orthogonal moves,
    # sqrt(2) for diagonal moves -- matches the edge-cost metric used by
    # A*, PA*, and path_cost(), so Dijkstra optimizes the same objective.
    return math.hypot(start[0]-end[0], start[1]-end[1])

def f(graph, start, end):
    return g(graph, start,end)    

def dijkstra(graph):
    # Here you need to implement Dijkstra's algorithm. Remember to modify it to stop when the shortest path to the
    # goal node has been found. The implementation should return the path from start to goal, in the form of a
    # sequential list of nodes in the path.

    start = tuple(graph.get_start_node())
    dest = tuple(graph.get_goal_node())

    vertices = graph.get_list_of_nodes()

    # initialize distance maps
    dist = {v: (float('infinity'),None) for v in vertices}
    dist[start] = (0, None)

    # Track a priority queue to pick the shortest next step
    pq = [(0, start)]

    current = start
    graph.add_visited_node(start)

    while len(pq):
        currdist, current = heapq.heappop(pq)

        # Stop only when the goal is POPPED: its distance label is final at
        # that point. Breaking when dest is first relaxed (pushed) could lock
        # in a non-optimal route before a cheaper one is dequeued.
        if current == dest:
            break

        if currdist > dist[current][0]:
            continue

        for next in graph.get_neighbors(current):
            graph.add_visited_node(next)
            newdist = currdist + f(graph, current, next)
            if newdist < dist[next][0]:
                dist[next] = (newdist,current)
                heapq.heappush( pq, (newdist, next) )


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


if __name__ == "__main__":
    graph = Graph(sys.argv[1])
    path = dijkstra(graph)

    print(path)
