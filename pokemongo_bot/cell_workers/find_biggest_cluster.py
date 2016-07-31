from pokemongo_bot.cell_workers.utils import distance, merc2coord, coord2merc
from networkx.algorithms.clique import find_cliques

import networkx as nx
import numpy as np


class FindBiggestCluster(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.dest = None

    def work(self):
        forts = self.bot.get_forts()
        radius = self.bot.config.navigator_radius
        self.dest = find_biggest_cluster(radius, forts)


def find_biggest_cluster(radius, points):
    graph = nx.Graph()
    for fort in points:
            f = fort['latitude'], fort['longitude']
            graph.add_node(f)
            for node in graph.nodes():
                if node != f and distance(f[0], f[1], node[0], node[1]) <= radius*2:
                    graph.add_edge(f, node)
    cliques = list(find_cliques(graph))
    if len(cliques) > 0:
        max_clique = max(list(find_cliques(graph)), key=len)
        merc_clique = [coord2merc(x[0], x[1]) for x in max_clique]
        clique_x, clique_y = zip(*merc_clique)
        best_point = np.mean(clique_x), np.mean(clique_y)
        best_coord = merc2coord(best_point)
        return {'latitude': best_coord[0], 'longitude': best_coord[1], 'num_forts': len(max_clique)}
    else:
        return None