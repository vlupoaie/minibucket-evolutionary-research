from utils.vector import Vector


class Node:
    def __init__(self, node_id, cost):
        self.id = node_id
        self.cost = cost
        self.neighbors = set()

    def __str__(self):
        return '<Node {} {} -> {}>'.format(self.id, self.cost, ', '.join(item.id for item in self.neighbors))

    def __repr__(self):
        return '<Node {} {} -> {}>'.format(self.id, self.cost, ', '.join(item.id for item in self.neighbors))

    def __lt__(self, other):
        if not isinstance(other, Node):
            raise TypeError('can only compare another node to node')
        return (self.id, self.cost) < (other.id, other.cost)

    def __len__(self):
        return len(self.neighbors)

    def __iter__(self):
        return iter(self.neighbors)

    def add_neighbor(self, node):
        self.neighbors.add(node)

    def split(self, pieces):
        self.cost = self.cost / pieces

    def json_serializable(self):
        return self.id


class Graph:
    def __init__(self):
        self.nodes = {}

    def __str__(self):
        return str(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, item):
        if isinstance(item, Node):
            return item.id in self.nodes
        return item in self.nodes

    def __iter__(self):
        return iter(self.nodes.values())

    def __getitem__(self, item):
        return self.nodes[item]

    def add_node(self, node_id, node_cost):
        if node_id in self.nodes:
            return self.nodes[node_id]
        new_node = Node(node_id, node_cost)
        node_cost.includes = {new_node}
        self.nodes[node_id] = new_node
        return new_node


def read_graph(graph_file):
    # read graph from file
    graph = Graph()
    original_graph = Graph()
    with open(graph_file, 'r') as h:
        for line in h:
            line = line.strip()
            if not line:
                continue

            line_type, line = line[:2].strip(), line[2:]

            # process new node or new edge
            if line_type == 'n':
                node_id, values = line.split(' ', 1)
                if node_id not in graph:
                    graph.add_node(node_id, Vector(*list(map(float, values.split()))))
                    original_graph.add_node(node_id, Vector(*list(map(float, values.split()))))
            elif line_type == 'e':
                node_id_1, node_id_2 = line.split()

                node_1, node_2 = graph[node_id_1], graph[node_id_2]
                node_1.add_neighbor(node_2)
                node_2.add_neighbor(node_1)

                node_1, node_2 = original_graph[node_id_1], original_graph[node_id_2]
                node_1.add_neighbor(node_2)
                node_2.add_neighbor(node_1)

    return graph, original_graph
