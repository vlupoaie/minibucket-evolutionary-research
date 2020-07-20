import sys
import os
from solvers.hybridization import Solver


# INSTANCE_DIR = "instances/bi-objective"
INSTANCE_DIR = sys.argv[1]


def run_instance(instance, max_vars):
    dimensions = int(instance.split("_d")[1])
    solver = Solver(instance, max_vars, dimensions, "bb")
    solver.run()


instances = os.listdir(INSTANCE_DIR)
for instance in instances:
    for i in [10, 10, 10, 10, 10, 10]:
        run_instance(instance, i)
