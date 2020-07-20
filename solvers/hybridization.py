import os
import json
import time
import argparse
from math import inf
from utils.vector import Vector
from solvers.genetic import NSGA2
from utils.graph import read_graph
from utils.result_set import ResultSet
from solvers.branchandbound import BranchAndBound
from minibucket.heuristics import get_variables_order, MiniBucket

ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
INSTANCES_DIR = os.path.join(ROOT, 'instances')
MONO_DIR = os.path.join(INSTANCES_DIR, 'mono-objective')
BI_DIR = os.path.join(INSTANCES_DIR, 'bi-objective')

RESULTS_DIR = os.path.join(ROOT, 'results')
BB_RESULTS = os.path.join(RESULTS_DIR, 'bb')
MONO = os.path.join(BB_RESULTS, 'mono-objective')
BI = os.path.join(BB_RESULTS, 'bi-objective')
if not os.path.isdir(RESULTS_DIR):
    os.mkdir(RESULTS_DIR)

if not os.path.isdir(BB_RESULTS):
    os.mkdir(BB_RESULTS)

if not os.path.isdir(MONO):
    os.mkdir(MONO)

if not os.path.isdir(BI):
    os.mkdir(BI)


parser = argparse.ArgumentParser(description='Solver MO-BB')
parser.add_argument("-i", "--instance", help="n10_ep0.5_d2")
parser.add_argument("-mbe", "--maxvars", help="2")
args = parser.parse_args()

INSTANCE = args.instance
DIMENSIONS = int(args.instance.split("_d")[1])
MINI_BUCKETS = int(args.maxvars)


def vertex_cover_cost(first_node, second_node):
    return {
        'headers': [first_node, second_node],
        0: ResultSet((Vector(*(inf for _ in range(len(first_node.cost)))),)),
        1: ResultSet((first_node.cost,)),
        2: ResultSet((second_node.cost,)),
        3: ResultSet((first_node.cost + second_node.cost,)),
    }


class Solver:
    def __init__(self, instance, minibuckets, dimensions, search_method):
        self.instance = instance
        self.minibuckets = minibuckets
        self.dimensions = dimensions
        self.search_method = search_method
        if self.dimensions == 1:
            self.path = os.path.join(MONO_DIR, instance)
        else:
            self.path = os.path.join(BI_DIR, instance)

        self.graph, self.original_graph = read_graph(self.path)

        self.order = get_variables_order(self.graph)
        self.original_order = get_variables_order(self.original_graph)
        self.heuristic_solver = MiniBucket(self.order, self.original_order, self.minibuckets, vertex_cover_cost,
                                           debug=False)
        self.heuristic_solver.build_buckets()
        if search_method == "bb":
            self.search_solver = BranchAndBound(self.heuristic_solver, len(self.graph))
        elif search_method == "nsga2":
            self.search_solver = NSGA2(self.order, self.heuristic_solver)

    def run(self):
        print("*" * 20, self.instance, "*" * 20)
        start = time.time()
        pareto_front = self.search_solver.run()
        elapsed_time = time.time() - start

        if self.dimensions == 1:
            f = open(os.path.join(MONO, "{}_mbe{}_{}".format(self.search_method, self.minibuckets,  self.instance)), 'w')
        else:
            f = open(os.path.join(BI, "{}_mbe{}_{}".format(self.search_method, self.minibuckets, self.instance)), 'w')
        f.write(json.dumps({"pareto_front": pareto_front.json_serializable(),
                            "data": str(pareto_front),
                            "time": round(elapsed_time, 2)}, indent=4))
        f.close()


# solver = Solver(INSTANCE, MINI_BUCKETS, DIMENSIONS, "bb")
# solver.run()








