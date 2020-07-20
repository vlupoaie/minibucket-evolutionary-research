import numbers
from math import inf


class Vector(tuple):
    def __new__(cls, *args, includes=None):
        result = super(Vector, cls).__new__(cls, args)
        if not includes:
            includes = set()
        setattr(result, 'includes', includes)
        return result

    def __str__(self):
        return '({}, includes={})'.format(', '.join(map(str, self)), ','.join(
            map(str, sorted(int(item.id) if item.id.isnumeric() else item.id for item in self.includes))) or '<None>')

    def __add__(self, other):
        if not isinstance(other, Vector):
            raise TypeError('can only add another vector to vector')
        if len(self) != len(other):
            raise TypeError('cannot add vector of different size')

        if self[0] == inf or other[0] == inf:
            new_includes = set()
            new_values = (inf for _ in range(len(self)))
        else:
            new_includes = self.includes | other.includes
            new_values = [sum(x) for x in zip(*(node.cost for node in new_includes))]

        return Vector(*new_values, includes=new_includes)

    def __truediv__(self, other):
        if not isinstance(other, numbers.Number):
            raise TypeError('can only divide by a number')
        return Vector(*(x / other for x in self), includes=self.includes)

    def __eq__(self, other):
        if not isinstance(other, Vector) and not isinstance(other, tuple):
            raise TypeError('can only compare vector to another vector or tuple')
        return all(x == y for x, y in zip(self, other))

    def __ne__(self, other):
        if not isinstance(other, Vector) and not isinstance(other, tuple):
            raise TypeError('can only compare vector to another vector or tuple')
        return not all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if not isinstance(other, Vector) and not isinstance(other, tuple):
            raise TypeError('can only compare vector to another vector or tuple')
        return self != other and all(x <= y for x, y in zip(self, other))

    def __le__(self, other):
        if not isinstance(other, Vector) and not isinstance(other, tuple):
            raise TypeError('can only compare vector to another vector or tuple')
        return all(x <= y for x, y in zip(self, other))

    def __gt__(self, other):
        if not isinstance(other, Vector) and not isinstance(other, tuple):
            raise TypeError('can only compare vector to another vector or tuple')
        return self != other and all(x >= y for x, y in zip(self, other))

    def __ge__(self, other):
        if not isinstance(other, Vector) and not isinstance(other, tuple):
            raise TypeError('can only compare vector to another vector or tuple')
        return all(x >= y for x, y in zip(self, other))

    def __hash__(self):
        return super(Vector, self).__hash__() + tuple(sorted(self.includes)).__hash__()

    @staticmethod
    def add_vectors(*vectors, dimensions=None):
        if not vectors:
            new_includes = set()
            new_values = (0 for _ in range(dimensions))
        elif any(v[0] == inf for v in vectors):
            new_includes = set()
            new_values = (inf for _ in range(len(vectors[0])))
        else:
            new_includes = set.union(*(v.includes for v in vectors))
            new_values = [sum(x) for x in zip(*(node.cost for node in new_includes))]

        return Vector(*new_values, includes=new_includes)
