#!/usr/bin/python
"""Progressive A* 
"""
from a_star import a_star, H

def HPA(graph, n, goal, last_best):
    return H(graph, n, goal)

def pa_star(levels, weight=1.0):
    last_best    = None
    ret          = None
    heuristic    = H
    for n in range(-1, -(len(levels)+1), -1):
        l_n   = levels[n]
        graph = l_n[0]
        scale = l_n[1]
        ret   = [(scale*v[0],scale*v[1]) for v in a_star(graph, weight, heuristic)] 
        
        if ret is not None:
            last_best   = ret
            heuristic   = lambda graph, n, g: HPA(graph, n, g, last_best) 

    return ret

