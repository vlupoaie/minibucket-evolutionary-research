import time
import random
from math import inf
from itertools import chain

from utils.result_set import ResultSet


class NSGA2:
    def __init__(self, order, heuristics, generations=100, population_size=100,
                 k_parents=2, crossover_chance=0.6, mutation_chance=0.4):
        self.order = order
        self.nodes_count = len(order)
        self.heuristics = heuristics
        self.dimensions = heuristics.dimensions
        self.generations = generations
        self.population_size = population_size
        self.sort_percentage = 0.5
        self.k_parents = min(population_size, k_parents)
        self.crossover_chance = crossover_chance
        self.mutation_chance = mutation_chance / self.nodes_count

        self.generate_strategy = 'random'
        # self.generate_strategy = 'prefix'
        # self.generate_strategy = 'heuristic'

        # self.crossover_strategy = 'partial_parent'
        self.crossover_strategy = 'majority'
        # self.crossover_strategy = 'vertex_cover'

        self.mutation_strategy = 'vertex_cover'
        # self.mutation_strategy = 'heuristic'

        self.this_population, self.next_population = self.generate_population()

    def run(self):
        for generation in range(self.generations):
            print('Generation', generation + 1)

            # crossover
            self.crossover()

            # mutation
            self.mutation()

            # sort population according to domination rank and crowding distance
            self.next_population = self.selection(*self.sort_population())
            self.this_population = self.copy_individuals(self.next_population)

            # self.crossover_chance *= 0.99
            # self.mutation_chance *= 1.1
            # print('Crossover {:.2f} - Mutation {:.3f}'.format(self.crossover_chance, self.mutation_chance))

    def generate_population(self):
        if self.generate_strategy == 'random':
            return self._generate_random_population()
        elif self.generate_strategy == 'prefix':
            return self._generate_prefix_population()
        elif self.generate_strategy == 'heuristic':
            return self._generate_heuristic_population()

    def _generate_random_population(self, zero_chance=0.2):
        populations = []

        # initialise chromosomes for current and next population
        for _ in range(2):
            population = []
            for count in range(self.population_size):
                chromosome = [0 if random.random() < zero_chance else 1 for _ in range(self.nodes_count)]
                new_individual = {
                    'chromosome': chromosome,
                    'cost': self.heuristics.compute_cost(chromosome)[0].pop()
                }
                population.append(new_individual)
            populations.append(population)

        return populations

    def _generate_prefix_population(self):
        populations = []

        viable = 2 * self.population_size
        min_length = len(bin(viable)) - 2
        counter = 0
        while viable:
            # get best assignment starting with this prefix
            partial_assignment = list(map(int, bin(counter)[2:].ljust(min_length, '0')))
            result, next_best = self.heuristics.compute_cost(partial_assignment)
            while not all(all(value == inf for value in cost) for cost in result) and \
                    len(partial_assignment) < self.nodes_count:
                partial_assignment.append(next_best)
                if len(partial_assignment) == self.nodes_count:
                    break
                result, next_best = self.heuristics.compute_cost(partial_assignment)

            # check if full solution and add to population
            if len(partial_assignment) == self.nodes_count:
                populations.append({
                    'chromosome': partial_assignment,
                    'cost': self.heuristics.compute_cost(partial_assignment)[0].pop()
                })
                viable -= 1

            counter += 1

        return populations[:self.population_size], populations[self.population_size:]

    def _generate_heuristic_population(self, heuristic_chance=0.5):
        populations = []

        # initialise chromosomes for current and next population
        for _ in range(2):
            population = []
            for count in range(self.population_size):
                chromosome = []
                for _ in range(self.nodes_count):
                    if random.random() < heuristic_chance:
                        _, next_best = self.heuristics.compute_cost(chromosome)
                        chromosome.append(next_best)
                    else:
                        chromosome.append(1)

                new_individual = {
                    'chromosome': chromosome,
                    'cost': self.heuristics.compute_cost(chromosome)[0].pop()
                }
                population.append(new_individual)
            populations.append(population)

        return populations

    def sort_population(self, combined=None, keep_best=None):
        # combine first and this population then sort and select next population
        combined = combined or (self.this_population + self.next_population)
        keep_best = keep_best or int(self.population_size * self.sort_percentage)

        # clean domination count and dominates for all individuals to be sorted
        for item in combined:
            if 'domination_count' in item:
                del item['domination_count']
            if 'dominates' in item:
                del item['dominates']
            if 'rank' in item:
                del item['rank']

        # compute domination rank for each chromosome
        first_front = []
        for first_count, first_individual in enumerate(combined):
            first_individual.setdefault('domination_count', 0)
            first_individual.setdefault('dominates', [])

            for second_individual in combined[first_count + 1:]:
                second_individual.setdefault('domination_count', 0)
                second_individual.setdefault('dominates', [])

                if first_individual['cost'] < second_individual['cost']:
                    first_individual['dominates'].append(second_individual)
                    second_individual['domination_count'] += 1
                elif first_individual['cost'] > second_individual['cost']:
                    second_individual['dominates'].append(first_individual)
                    first_individual['domination_count'] += 1

            # check if first individual belongs to the first front
            if not first_individual['domination_count']:
                first_individual['rank'] = 0
                first_front.append(first_individual)

        print('First front ({})'.format(len(first_front)), [item['cost'] for item in first_front][:10])

        # build next fronts starting from first front
        counter = 0
        fronts = [first_front]
        already_added = len(first_front)
        while already_added < keep_best:
            next_front = []
            for individual in fronts[counter]:
                for dominated in individual['dominates']:
                    dominated['domination_count'] -= 1
                    if not dominated['domination_count']:
                        dominated['rank'] = counter + 1
                        next_front.append(dominated)
            counter += 1
            already_added += len(next_front)
            fronts.append(next_front)

        # add other as last front in order to assign them a rank and a distance for tournament selection
        last_front = []
        for individual in combined:
            if 'rank' in individual:
                continue
            individual['rank'] = counter + 1
            last_front.append(individual)
        if last_front:
            fronts.append(last_front)

        # compute crowding distance on each front
        self.crowding_distance(fronts)

        # select best individuals according to crowding domination
        if last_front:
            return sorted(chain(*fronts[:-1]), key=lambda x: (x['rank'], -x['distance']))[:keep_best], last_front
        else:
            return sorted(chain(*fronts), key=lambda x: (x['rank'], -x['distance']))[:self.population_size], last_front

    @staticmethod
    def crowding_distance(fronts):
        for front in fronts:
            # initialize distances
            for individual in front:
                individual['distance'] = 0

            # for each objective sort and add distance
            objectives_count = len(front[0]['cost'])
            for dimension in range(objectives_count):
                sorted_front = sorted(front, key=lambda x: x['cost'][dimension])

                # save min and max values of this objective to normalize
                min_value = sorted_front[0]['cost'][dimension]
                max_value = sorted_front[-1]['cost'][dimension]
                factor = (max_value - min_value) or 10 ** -6

                # keep the most extreme solutions of this front
                sorted_front[0]['distance'] = sorted_front[-1]['distance'] = inf

                # update distance for each individual that is not an edge of the front
                for position, individual in enumerate(sorted_front[1:-1], 1):
                    individual['distance'] += (sorted_front[position + 1]['cost'][dimension] -
                                               sorted_front[position - 1]['cost'][dimension]) / factor

    def selection(self, temp_population, remaining):
        # tournament selection using rank and crowding distance
        while len(temp_population) < self.population_size:
            first, second = random.sample(remaining, 2)
            if (first['rank'], -first['distance']) < (second['rank'], -second['distance']):
                chosen = first
            else:
                chosen = second
            new_individual = self.copy_individual(chosen)
            temp_population.append(new_individual)
        return temp_population

    def crossover(self):
        if self.crossover_strategy == 'partial_parent':
            return self._partial_parent_crossover()
        elif self.crossover_strategy == 'majority':
            return self._majority_crossover()
        elif self.crossover_strategy == 'vertex_cover':
            return self._vertex_cover_crossover()

    def _partial_parent_crossover(self):
        for count in range(int(self.population_size * self.crossover_chance)):
            chosen_parents = random.sample(self.next_population, self.k_parents)
            new_individual = {'chromosome': [], 'cost': None}

            # choose each position according to best partial assignment of parent
            for position in range(self.nodes_count):
                # compute all partial assignments of the chosen parents
                parent_costs = []
                result_set = ResultSet()
                for parent in chosen_parents:
                    this_cost = self.heuristics.compute_cost(parent['chromosome'][:position + 1])[0]
                    parent_costs.append(this_cost)
                    result_set |= this_cost
                best_cost, index = max((len(result_set & cost), count) for count, cost in enumerate(parent_costs))
                new_individual['chromosome'].append(chosen_parents[index]['chromosome'][position])

            # compute cost of new individual
            new_individual['cost'] = self.heuristics.compute_cost(new_individual['chromosome'])[0].pop()

            # replace worst parent with new child
            worst_parent = min(chosen_parents, key=lambda k: k['cost'])
            self.next_population.remove(worst_parent)
            self.next_population.append(new_individual)

    def _majority_crossover(self):
        for count in range(int(self.population_size * self.crossover_chance)):
            chosen_parents = random.sample(self.next_population, self.k_parents)
            new_individual = {'chromosome': [], 'cost': None}

            # choose each position either using MBE heuristic or the majority of the parents
            for position in range(self.nodes_count):
                if all(parent['chromosome'][position] == 1 for parent in chosen_parents):
                    new_individual['chromosome'].append(1)
                elif all(parent['chromosome'][position] == 0 for parent in chosen_parents):
                    new_individual['chromosome'].append(0)
                else:
                    partial_cost, next_best = self.heuristics.compute_cost(new_individual['chromosome'])
                    new_individual['chromosome'].append(next_best)

            # compute cost of new individual and add to population
            new_individual['cost'] = self.heuristics.compute_cost(new_individual['chromosome'])[0].pop()
            self.next_population.append(new_individual)

    def _vertex_cover_crossover(self):
        for count in range(int(self.population_size * self.crossover_chance)):
            first_parent, second_parent = random.sample(self.next_population, 2)
            first_child, second_child = self.copy_individual(first_parent), self.copy_individual(second_parent)

            # choose random node to swap hard constraint solution for
            position = random.randrange(0, self.nodes_count)
            chosen_node = self.order[position]

            first_chromosome = first_child['chromosome']
            second_chromosome = second_child['chromosome']
            first_chromosome[position], second_chromosome[position] = \
                second_chromosome[position], first_chromosome[position]
            for neighbor in chosen_node.neighbors:
                position = self.order.index(neighbor)
                first_chromosome[position], second_chromosome[position] = \
                    second_chromosome[position], first_chromosome[position]

            # add new nodes to population
            first_child['cost'] = self.heuristics.compute_cost(first_child['chromosome'])[0].pop()
            second_child['cost'] = self.heuristics.compute_cost(second_child['chromosome'])[0].pop()
            self.next_population.append(first_child)
            self.next_population.append(second_child)

    def mutation(self):
        if self.mutation_strategy == 'vertex_cover':
            return self._vertex_cover_mutation()
        elif self.mutation_strategy == 'heuristic':
            return self._heuristic_mutation()

    def _vertex_cover_mutation(self):
        # vertex cover specific mutation
        for individual in self.next_population:
            changed = False
            for position in range(self.nodes_count):
                random_number = random.random()
                if random_number < self.mutation_chance / 2:
                    # if change from 1 to 0 set neighbors to 1; if change from 0 to 1 set neighbors to 0
                    value = individual['chromosome'][position]
                    individual['chromosome'][position] = 1 - value
                    node = self.order[position]
                    for neighbor in node.neighbors:
                        individual['chromosome'][self.order.index(neighbor)] = value
                    changed = True
                elif random_number < self.mutation_chance:
                    individual['chromosome'][position] = 1 - individual['chromosome'][position]
                    changed = True
            if changed:
                individual['cost'] = self.heuristics.compute_cost(individual['chromosome'])[0].pop()

    def _heuristic_mutation(self):
        # use heuristics to decide new value for a given position
        for individual in self.next_population:
            changed = False
            for position in range(self.nodes_count):
                random_number = random.random()
                if random_number < self.mutation_chance / 2:
                    this_chromosome = individual['chromosome']
                    _, next_best = self.heuristics.compute_cost(this_chromosome[:position])
                    this_chromosome[position] = next_best
                    changed = True
                elif random_number < self.mutation_chance:
                    individual['chromosome'][position] = 1 - individual['chromosome'][position]
                    changed = True
            if changed:
                individual['cost'] = self.heuristics.compute_cost(individual['chromosome'])[0].pop()

    @staticmethod
    def copy_individuals(individuals):
        return [NSGA2.copy_individual(individual) for individual in individuals]

    @staticmethod
    def copy_individual(individual):
        return {
            'chromosome': list(individual['chromosome']),
            'cost': individual['cost'],
            'rank': individual.get('rank'),
            'distance': individual.get('distance'),
        }
