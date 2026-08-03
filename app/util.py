import numpy as np
from PIL import Image

VERMILLION = (213, 94, 0, 255)
BLUE_GREEN = (0, 158, 115, 255)
SKY_BLUE = (86, 180, 233, 255)
REDDISH_PURPLE = (204, 121, 167, 255)


class Graph:
    def __init__(self, image_file, display=True):
        img = Image.open(image_file)
        self.arr = np.array(img)
        self.start = None
        self.goal = None
        self.obstacle_map = np.zeros([self.arr.shape[0], self.arr.shape[1]])
        goal_color = np.array([255, 0, 0, 255])
        start_color = np.array([0, 255, 0, 255])
        obstacle_color = np.array([0, 0, 0, 255])
        self.visited_color = np.array(SKY_BLUE)

        self.map_changed = True
        self.nodes = []

        self.fig = None
        self.img = None

        for i in range(self.arr.shape[0]):
            for j in range(self.arr.shape[1]):
                pixel = self.arr[i][j]
                if np.array_equal(pixel, goal_color):
                    self.goal = [i, j]
                    self.nodes.append(tuple(self.goal))
                    self.arr[i][j] = np.array(VERMILLION)

                elif np.array_equal(pixel, start_color):
                    self.start = [i, j]
                    self.nodes.append(tuple(self.start))
                    self.arr[i][j] = np.array(BLUE_GREEN)

                elif np.array_equal(pixel, obstacle_color):
                    self.obstacle_map[i][j] = 1

                else:
                    self.nodes.append((i, j))

    def get_list_of_nodes(self):
        return self.nodes

    def get_neighbors(self, node):

        neighbors = []

        height, width  = self.obstacle_map.shape
        for x, y in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
            try:
                potential_neighbor = [node[0] + x, node[1] + y]
                if potential_neighbor[0] < 0 or potential_neighbor[1] < 0:
                    continue

                if potential_neighbor[0] >= height or potential_neighbor[1] >= width:
                    continue

                if self.obstacle_map[potential_neighbor[0]][potential_neighbor[1]] == 0:
                    neighbors.append(tuple(potential_neighbor))

            except IndexError:
                continue

        return neighbors

    def add_visited_node(self, node):
        if node != tuple(self.start) and node != tuple(self.goal):
            self.arr[node[0]][node[1]] = self.visited_color

        self.visualize_map()

    def visualize_map(self):
        if self.img == None:
            return
         
        self.img.set_data(self.arr)

    def add_shortest_path(self, path):
        path_color = np.array(REDDISH_PURPLE)
        for node in path:
            if node != tuple(self.start) and node != tuple(self.goal):
                self.arr[node[0]][node[1]] = path_color
        self.visualize_map()

    def get_start_node(self):
        return self.start

    def get_goal_node(self):
        return self.goal
