
class BranchAndBound:
    def __init__(self, mbe_solver, n):
        self.nr_vertices = n
        self.mbe_solver = mbe_solver
        self.pareto_front = None
        self.max_branches = pow(2, n)
        self.last_progress = 0

    def init_paretofront(self, path):
        if len(path) == self.nr_vertices:
            cost, ba = self.mbe_solver.compute_cost(path)
            self.pareto_front = cost
            return
        cost, best_next_assignment = self.mbe_solver.compute_cost(path)
        path += [best_next_assignment]
        self.init_paretofront(path)

    def add_solution(self, path):
        cost, ba = self.mbe_solver.compute_cost(path)
        new_progress = round(int(''.join(map(str, path)), 2)/self.max_branches, 2)
        if self.last_progress != new_progress:
            print("Progress: {}%".format(int(new_progress * 100)))
            self.last_progress = new_progress
        self.pareto_front = self.pareto_front.__or__(cost)

    def bound(self, path):
        cost, ba = self.mbe_solver.compute_cost(path)
        return cost.__gt__(self.pareto_front)

    def branch(self, path):
        if self.bound(path):
            return

        if len(path) == self.nr_vertices:
            self.add_solution(path)
            return

        for j in range(0, 2):
            path.append(j)
            self.branch(path)
            path[-1:] = []

    def run(self):
        self.init_paretofront([0])
        self.branch([])
        return self.pareto_front



