import os
import random
import argparse
from itertools import product

INSTANCES_DIR = os.path.join(os.path.abspath(os.path.join(__file__, os.pardir)), 'instances')
MONO_DIR = os.path.join(INSTANCES_DIR, 'mono-objective')
BI_DIR = os.path.join(INSTANCES_DIR, 'bi-objective')

if not os.path.isdir(INSTANCES_DIR):
    os.mkdir(INSTANCES_DIR)

if not os.path.isdir(MONO_DIR):
    os.mkdir(MONO_DIR)

if not os.path.isdir(BI_DIR):
    os.mkdir(BI_DIR)

SCORE_LOWER_BOUND = 0
SCORE_UPPER_BOUND = 200

parser = argparse.ArgumentParser(description='Instance Generator')
parser.add_argument("-n", "--nodes", help="Ex: [50, 100]")
parser.add_argument("-ep", "--edgesp", help="Ex: [0.1, 0.2]")
parser.add_argument("-d", "--dimensions", help="Ex: [1, 2]")
args = parser.parse_args()

nodes = eval(args.nodes)
ep = eval(args.edgesp)
d = eval(args.dimensions)
instances = list(product(nodes, ep, d))

for instance in instances:
    NODES = instance[0]
    EDGE_PERCENTAGE = instance[1]
    DIMENSIONS = instance[2]
    if DIMENSIONS == 1:
        path = os.path.join(MONO_DIR, 'n{}_ep{}_d{}'.format(NODES, EDGE_PERCENTAGE, DIMENSIONS))
    else:
        path = os.path.join(BI_DIR, 'n{}_ep{}_d{}'.format(NODES, EDGE_PERCENTAGE, DIMENSIONS))
    output = open(path, 'w')
    for i in range(NODES):
        output.write('n {} {}\n'.format(i + 1, ' '.join(
            map(str, (random.randint(SCORE_LOWER_BOUND, SCORE_UPPER_BOUND) for _ in range(DIMENSIONS))))))

    nodes_covered = set()
    edges_count = 0
    for i in range(NODES):
        for j in range(i + 1, NODES):
            if random.random() < EDGE_PERCENTAGE:
                output.write('e {} {}\n'.format(i + 1, j + 1))
                nodes_covered.add(i + 1)
                nodes_covered.add(j + 1)
                edges_count += 1

    print(nodes_covered, NODES)
    if len(nodes_covered) != NODES:
        for i in range(1, NODES+1):
            if i not in nodes_covered:
                print("***", i)
                output.write('e {} {}\n'.format(i, i + 1))
                edges_count += 1
    print('Generated {} nodes with {} edges'.format(NODES, edges_count))
    output.write('g {} {}\n'.format(NODES, edges_count))
