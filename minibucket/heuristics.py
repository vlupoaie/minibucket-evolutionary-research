import random
from functools import lru_cache
from math import inf
from itertools import chain

from utils.result_set import ResultSet
from utils.vector import Vector

DEBUG = True


def get_variables_order(graph, heuristic='min-neighbors', custom_order=None):
    if not heuristic:
        return sorted(graph, key=lambda k: k.id)
    elif heuristic == 'min-neighbors':
        return sorted(graph, key=len, reverse=True)
    elif heuristic == 'min-fill':
        pass
    elif heuristic == 'custom':
        return sorted(graph, key=lambda k: custom_order.index(k.id))


class MiniBucket:
    def __init__(self, order, original_order, max_variables, cost_function, debug=None):
        self.order = order
        self.original_order = original_order
        self.dimensions = len(self.order[0].cost)  # nr of objectives
        self.reverse_order = list(reversed(order))
        self.max_variables = max_variables
        self.cost_function = cost_function
        self.buckets = {}
        self.debug = debug if debug is not None else DEBUG

    def build_buckets(self):
        self.compute_buckets()
        self.compute_heuristics()
        self.print_final()

    def compute_buckets(self):
        processed = set()
        for node in self.reverse_order:
            constraints = [item for item in node if item not in processed]
            elementary_costs = self.build_costs(node, constraints)
            self.buckets[node] = {'costs': elementary_costs, 'heuristics': []}
            processed.add(node)

    def build_costs(self, node, constraints):
        elementary_costs = []

        # add all elementary costs to this bucket
        for other_node in constraints:
            elementary_cost = self.cost_function(node, other_node)
            elementary_costs.append(elementary_cost)

        return elementary_costs

    def create_cost_table(self, headers):
        cost_table = {'headers': list(headers)}
        for i in range(2 ** len(headers)):
            # sum costs of chosen nodes
            total_cost = Vector.add_vectors(
                *(node.cost for count, node in enumerate(headers) if i & (1 << count)), dimensions=self.dimensions)
            cost_table[i] = ResultSet((total_cost,))
        return cost_table

    @staticmethod
    def add_tables(big_table, small_table):
        big_headers = big_table['headers']
        small_headers = small_table['headers']

        # add small cost tables together
        for small_key, small_value in small_table.items():
            if small_key in {'headers', 'from'}:
                continue

            # build index, mask and common cost
            index, mask = MiniBucket.get_index_mask_cost(small_key, small_headers, big_headers)

            # add to corresponding big table keys
            for big_key in big_table:
                if big_key in {'headers', 'from'}:
                    continue
                if big_key & mask == index:
                    big_table[big_key] += small_value

    @staticmethod
    def get_index_mask_cost(key, old_headers, new_headers):
        index = mask = 0
        for old_count, node in enumerate(old_headers):
            is_set = bool(key & (1 << old_count))
            new_count = new_headers.index(node)
            mask += 1 << new_count
            index += is_set << new_count
        return index, mask

    @staticmethod
    def print_cost_table(cost_table, debug=True):
        if not debug:
            return
        headers = cost_table['headers']
        headers_length = len(headers)
        if 'from' in cost_table:
            print('From: {}'.format(cost_table['from'].id))
        print(' '.join(map(lambda x: str(x.id), headers)), 'Cost')
        for i in range(2 ** headers_length):
            print(' '.join(reversed(bin(i)[2:].zfill(headers_length))), cost_table[i])
        print()

    def compute_heuristics(self):
        for node_count, node in enumerate(self.reverse_order):
            if self.debug:
                print('==>> Computing minibuckets for node:', node)

            # add together cost and all heuristics
            costs = self.buckets[node]['costs']
            heuristics = self.buckets[node]['heuristics']
            dependencies = costs + heuristics
            if self.debug:
                print('Dependencies count:', len(dependencies))
                for dep in dependencies:
                    self.print_cost_table(dep, self.debug)

            # split all dependencies to minibuckets
            minibuckets = self.get_minibuckets(dependencies, self.max_variables)
            if self.debug:
                print('Minibuckets count:', len(minibuckets))
                print('Splitting node:', node)
            node.split(len(minibuckets))

            # compute next node for each minibucket's heuristic
            ordered_minibuckets = []
            for minibucket in minibuckets:
                full_headers = set(chain.from_iterable((table['headers'] for table in minibucket)))
                for next_index, next_node in enumerate(self.reverse_order[node_count + 1:]):
                    if next_node in full_headers:
                        ordered_minibuckets.append((next_index, minibucket))
                        break
            ordered_minibuckets = [item[1] for item in sorted(ordered_minibuckets, key=lambda k: k[0])]

            # process each minibucket individually
            for count, minibucket in enumerate(ordered_minibuckets):
                if self.debug:
                    print('Minibucket {} ({} functions):'.format(count + 1, len(minibucket)))
                    for function in minibucket:
                        self.print_cost_table(function, self.debug)
                full_headers = set(chain.from_iterable((table['headers'] for table in minibucket)))
                full_table = self.create_cost_table(full_headers)

                # compute heuristic for this minibucket
                for table in minibucket:
                    self.add_tables(full_table, table)
                if self.debug:
                    print('Summed minibucket:')
                    self.print_cost_table(full_table, self.debug)

                # add heuristic to the bucket of the first constraint in the chain
                for next_node in self.reverse_order[node_count + 1:]:
                    if next_node in full_headers:
                        reduced_table = self.eliminate_variable(full_table, node)
                        if self.debug:
                            print('Remaining reduced table:')
                            self.print_cost_table(reduced_table, self.debug)
                        self.buckets[next_node]['heuristics'].append(reduced_table)
                        break
            if self.debug:
                print('\n')

    @staticmethod
    def get_minibuckets(tables, max_variables):
        not_chosen = list(tables)
        minibuckets = []

        # build minibuckets as long as there are still costs not included
        while not_chosen:
            first_item = sorted(not_chosen, key=lambda k: len(k['headers']))[0]
            not_chosen.remove(first_item)
            variables = set(first_item['headers'])
            minibucket = [first_item]
            minibuckets.append(minibucket)

            # greedily add as many dependencies as possible to this bucket
            remaining = max_variables - len(variables)
            while remaining >= 0 and not_chosen:
                best_choice = MiniBucket.choose_next_function(variables, not_chosen, remaining)
                if best_choice is None:
                    break
                minibucket.append(best_choice)
                not_chosen.remove(best_choice)
                variables.update(best_choice['headers'])
                remaining = max_variables - len(variables)

        return minibuckets

    @staticmethod
    def choose_next_function(variables, not_chosen, remaining_variables):
        best_choice = None
        max_value = -inf
        for dependency in not_chosen:
            headers = set(dependency['headers'])
            common_variables = len(headers & variables)
            new_variables = len(headers - variables)

            # if not new variables are added then add to bucket
            if not new_variables:
                return dependency

            # check not to add too many variables
            if new_variables > remaining_variables:
                continue

            # greedily choose best rate of old to new variables
            value = common_variables / new_variables
            if value > max_value:
                best_choice = dependency
                max_value = value

        return best_choice

    @staticmethod
    def eliminate_variable(table, node):
        full_headers = table['headers']
        heuristic_headers = [item for item in full_headers if item != node]
        heuristic_table = {'headers': heuristic_headers, 'from': node}
        heuristic_table.update({i: ResultSet() for i in range(2 ** len(heuristic_headers))})
        if len(full_headers) == 1:
            raise Exception('Should not happen')

        # populate heuristic with joint non-dominated values
        for heuristic_key, value in heuristic_table.items():
            if heuristic_key in {'headers', 'from'}:
                continue

            # build index and mask
            index, mask = MiniBucket.get_index_mask_cost(heuristic_key, heuristic_headers, full_headers)

            # join corresponding full table keys
            for full_key in table:
                if full_key in {'headers', 'from'}:
                    continue
                if full_key & mask == index:
                    heuristic_table[heuristic_key] |= table[full_key]

        return heuristic_table

    def print_final(self):
        final_node = self.buckets[self.order[0]]
        all_headers = set()
        for cost in final_node['costs'] + final_node['heuristics']:
            all_headers.update(cost['headers'])
        final_cost = self.create_cost_table(all_headers)
        for cost in final_node['costs'] + final_node['heuristics']:
            self.add_tables(final_cost, cost)

        # remove dominated values
        for key, value in final_cost.items():
            if key in {'headers', 'from'}:
                continue
            value.remove_dominated()

        self.print_cost_table(final_cost, debug=True)

    # noinspection DuplicatedCode
    def compute_cost(self, assignment):
        assigned_count = len(assignment)

        # check if full cost or partial assignment heuristic
        if assigned_count == len(self.original_order):
            return self._compute_cost_full(assignment)
        else:
            return self._compute_cost_partial(assignment)

    def _compute_cost_full(self, assignment):
        zipped = list(zip(assignment, self.original_order))
        total_cost = None
        nodes_included = {node for value, node in zipped if value}

        for count, (first_value, first_node) in enumerate(zipped):

            # check if any hard constraints violated
            for second_value, second_node in zipped[count:]:
                if not first_value and not second_value:
                    if second_node in first_node.neighbors:
                        return ResultSet((Vector(*(inf for _ in range(self.dimensions)),
                                                 includes=nodes_included),)), None

            # add total cost from cost functions
            if first_value:
                total_cost = first_node.cost if total_cost is None else \
                    total_cost + first_node.cost

        return ResultSet((total_cost,)), None

    def _compute_cost_partial_backup(self, assignment):
        assigned_count = len(assignment)

        # try each value of the next unassigned variable
        assigned_nodes = set(self.order[:assigned_count + 1])
        possible_results = ResultSet()
        for possible_value in (0, 1):
            this_result = None
            this_assignment = assignment + [possible_value]

            # compute sum of costs for assigned variables
            for node in assigned_nodes:
                # add actual constraints and heuristics coming from unassigned nodes
                for cost_function in self.buckets[node]['costs'] + self.buckets[node]['heuristics']:
                    if 'from' in cost_function and cost_function['from'] in assigned_nodes:
                        continue
                    key = self.get_assignment_table_key(this_assignment, cost_function['headers'])
                    if not this_result:
                        this_result = cost_function[key]
                    else:
                        this_result = this_result + cost_function[key]
                    if all(item == tuple(inf for _ in range(self.dimensions)) for item in this_result):
                        return this_result, random.choice((0, 1))

            # save possible results
            possible_results |= this_result

        # check which is the next best value
        next_node = self.order[assigned_count]
        for result in possible_results:
            if next_node in result.includes:
                return possible_results, 1
            else:
                return possible_results, 0

    def _compute_cost_partial(self, assignment):
        assigned_count = len(assignment)
        assigned_nodes = tuple(self.order[:assigned_count + 1])

        # try each value of the next unassigned variable
        possible_results = ResultSet()
        for possible_value in (0, 1):

            this_assignment = tuple(assignment) + (possible_value,)
            this_result = self._compute_fixed_partial(this_assignment, assigned_nodes)

            # save possible results
            possible_results |= this_result

        # check which is the next best value
        next_node = self.order[assigned_count]
        for result in possible_results:
            if next_node not in result.includes:
                return possible_results, 0
            else:
                return possible_results, 1

    @lru_cache(maxsize=327680)
    def _compute_fixed_partial(self, partial, full):
        if not partial:
            return None

        assignment_length = len(partial)
        previous_partial = partial[:-1]

        this_result = self._compute_fixed_partial(previous_partial, full)
        if this_result and all(item == tuple(inf for _ in range(self.dimensions)) for item in this_result):
            return this_result

        node = self.order[assignment_length - 1]
        full_set = set(full)
        for cost_function in self.buckets[node]['costs'] + self.buckets[node]['heuristics']:
            if 'from' in cost_function and cost_function['from'] in full_set:
                continue
            key = self.get_assignment_table_key(partial, cost_function['headers'])
            if not this_result:
                this_result = cost_function[key]
            else:
                this_result = this_result + cost_function[key]
            if all(item == tuple(inf for _ in range(self.dimensions)) for item in this_result):
                return this_result
        return this_result

    def get_assignment_table_key(self, assignment, headers):
        key = 0
        for value, node in zip(assignment, self.order):
            try:
                key += value << headers.index(node)
            except ValueError:
                continue
        return key

    def get_best_next(self, assignment):
        assigned_count = len(assignment)

        # check if full cost or partial assignment heuristic
        if assigned_count == len(self.original_order):
            return None
        return self._next_best_assignment(tuple(assignment))

    @lru_cache(maxsize=327680)
    def _next_best_assignment(self, assignment):
        # try each value of the next unassigned variable
        possible_results = ResultSet()
        results = {}
        for possible_value in (0, 1):
            this_assignment = tuple(assignment) + (possible_value,)
            this_result = None
            this_index = len(this_assignment) - 1

            # add costs in this bucket
            node = self.order[this_index]
            for cost_function in self.buckets[node]['costs'] + self.buckets[node]['heuristics']:
                key = self.get_assignment_table_key(this_assignment, cost_function['headers'])
                if not this_result:
                    this_result = cost_function[key]
                else:
                    this_result = this_result + cost_function[key]
                if all(item == tuple(inf for _ in range(self.dimensions)) for item in this_result):
                    break

            # save result for this value - majority vote when returning
            results[possible_value] = this_result

            # save possible results
            possible_results |= this_result

        # check which is the next best value
        total_results = len(possible_results)
        if len(results[1] & possible_results) > total_results / 2:
            return 1
        else:
            return 0
