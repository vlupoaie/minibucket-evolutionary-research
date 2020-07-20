import os
import time
from math import inf

from minibucket.heuristics import get_variables_order, MiniBucket
from solvers.genetic import NSGA2
from utils.graph import read_graph
from utils.result_set import ResultSet
from utils.vector import Vector

MAX_MINIBUCKET_VARIABLES = 10


def vertex_cover_cost(first_node, second_node):
    return {
        'headers': [first_node, second_node],
        0: ResultSet((Vector(*(inf for _ in range(len(first_node.cost)))),)),
        1: ResultSet((first_node.cost,)),
        2: ResultSet((second_node.cost,)),
        3: ResultSet((first_node.cost + second_node.cost,)),
    }


def main():
    start_time = time.perf_counter()
    # input_file = 'inputs/test.txt'
    input_file = 'inputs/test2.txt'
    # input_file = 'inputs/test3.txt'
    # input_file = 'instances/mono-objective/n10_ep0.2_d1'
    # input_file = 'instances/bi-objective/n30_ep0.2_d2'
    # input_file = 'instances/bi-objective/n50_ep0.5_d2'
    # input_file = 'instances/bi-objective/n100_ep0.2_d2'
    # input_file = 'instances/bi-objective/n100_ep0.5_d2'
    # input_file = 'instances/bi-objective/n100_ep0.8_d2'
    # input_file = 'inputs/slide.txt'
    # input_file = 'inputs/graph2.txt'
    # input_file = 'inputs/medium_graph.txt'
    # input_file = 'inputs/big_graph.txt'
    graph, original_graph = read_graph(input_file)
    input_name = os.path.basename(input_file) + '_{}'.format(MAX_MINIBUCKET_VARIABLES)

    print('Graph:')
    print(graph)
    print()

    # order = get_variables_order(graph, heuristic=None)
    # order = get_variables_order(graph, heuristic='custom', custom_order='ADBECF')
    order = get_variables_order(graph)
    original_order = get_variables_order(original_graph)

    print('Order:')
    print(order)
    print()

    solver = MiniBucket(order, original_order, MAX_MINIBUCKET_VARIABLES, vertex_cover_cost, debug=False)
    solver.build_buckets()

    print('Finished building minibuckets ({} max vars) in {:.3f}s\n'.format(
        MAX_MINIBUCKET_VARIABLES, time.perf_counter() - start_time))

    assignment = [1, 0, 1, 1]
    cost, best_next_assignment = solver.compute_cost(assignment)
    new_next = solver.get_best_next(assignment)
    print(cost, best_next_assignment, new_next)


def genetic():
    start_time = time.perf_counter()

    # input_file = 'inputs/test.txt'
    # input_file = 'inputs/test2.txt'
    # input_file = 'inputs/test3.txt'
    # input_file = 'inputs/slide.txt'
    # input_file = 'inputs/graph2.txt'
    # input_file = 'inputs/medium_graph.txt'
    # input_file = 'inputs/big_graph.txt'
    # input_file = 'instances/mono-objective/n10_ep0.2_d1'
    # input_file = 'instances/bi-objective/n30_ep0.2_d2'
    # input_file = 'instances/bi-objective/n30_ep0.5_d2'
    # input_file = 'instances/bi-objective/n30_ep0.8_d2'
    # input_file = 'instances/bi-objective/n40_ep0.2_d2'
    input_file = 'instances/bi-objective/n40_ep0.5_d2'
    # input_file = 'instances/bi-objective/n40_ep0.8_d2'
    # input_file = 'instances/bi-objective/n50_ep0.5_d2'
    # input_file = 'instances/bi-objective/n60_ep0.2_d2'
    # input_file = 'instances/bi-objective/n100_ep0.2_d2'
    # input_file = 'instances/bi-objective/n100_ep0.5_d2'
    # input_file = 'instances/bi-objective/n100_ep0.8_d2'

    graph, original_graph = read_graph(input_file)
    input_name = os.path.basename(input_file) + '_{}'.format(MAX_MINIBUCKET_VARIABLES)

    order = get_variables_order(graph)
    original_order = get_variables_order(original_graph)
    solver = MiniBucket(order, original_order, MAX_MINIBUCKET_VARIABLES, vertex_cover_cost, debug=False)
    solver.build_buckets()

    print('Finished building minibuckets ({} max vars) in {:.3f}s\n'.format(
        MAX_MINIBUCKET_VARIABLES, time.perf_counter() - start_time))

    try:
        ga = NSGA2(order, solver)
        ga.run()
    except KeyboardInterrupt:
        pass

    print('Finished GA: {:.3f}s'.format(time.perf_counter() - start_time))


if __name__ == '__main__':
    main()
    # genetic()
