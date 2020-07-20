import operator
from math import inf

COMPARE_OPERATORS = {
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
}


class ResultSet(set):
    def __init__(self, *args, compare='<=', **kwargs):
        super(ResultSet, self).__init__(*args, **kwargs)
        self.compare = compare if callable(compare) else COMPARE_OPERATORS[compare]

    def __add__(self, other):
        new_items = set()
        if isinstance(other, ResultSet):
            for other_item in other:
                for self_item in self:
                    new_items.add(self_item + other_item)
        else:
            for item in self:
                new_items.add(item - other)
        return ResultSet(new_items)

    def __iadd__(self, other):
        new_items = set()
        if isinstance(other, ResultSet):
            for other_item in other:
                for self_item in self:
                    new_items.add(self_item + other_item)
        else:
            for item in self:
                new_items.add(item + other)
        self.clear()
        self.update(new_items)
        return self

    def __sub__(self, other):
        new_items = set()
        if isinstance(other, ResultSet):
            for other_item in other:
                for self_item in self:
                    new_items.add(self_item - other_item)
        else:
            for item in self:
                new_items.add(item - other)
        return ResultSet(new_items)

    def __isub__(self, other):
        new_items = set()
        if isinstance(other, ResultSet):
            for other_item in other:
                for self_item in self:
                    new_items.add(self_item - other_item)
        else:
            for item in self:
                new_items.add(item - other)
        self.clear()
        self.update(new_items)
        return self

    def __or__(self, other):
        to_return = ResultSet(super(ResultSet, self).__or__(other))
        to_return.remove_dominated()
        return to_return

    def __ior__(self, other):
        super(ResultSet, self).__ior__(other)
        self.remove_dominated()
        return self

    def __str__(self):
        return '{{{}}}'.format(', '.join(map(str, self)))

    def __eq__(self, other):
        if not isinstance(other, ResultSet):
            raise TypeError('can only compare result set to another result set')
        return all(x == y for x in self for y in other)

    def __ne__(self, other):
        if not isinstance(other, ResultSet):
            raise TypeError('can only compare result set to another result set')
        return not all(x == y for x in self for y in other)

    def __lt__(self, other):
        if not isinstance(other, ResultSet):
            raise TypeError('can only compare result set to another result set')
        return self != other and all(x <= y for x in self for y in other)

    def __le__(self, other):
        if not isinstance(other, ResultSet):
            raise TypeError('can only compare result set to another result set')
        return all(x <= y for x in self for y in other)

    def __gt__(self, other):
        if not isinstance(other, ResultSet):
            raise TypeError('can only compare result set to another result set')
        return self != other and all(x >= y for x in self for y in other)

    def __ge__(self, other):
        if not isinstance(other, ResultSet):
            raise TypeError('can only compare result set to another result set')
        return all(x >= y for x in self for y in other)

    def remove_redundant(self):
        contents = list(self)

        # remove infinity
        for first_count, first_item in enumerate(contents):
            if any(component == inf for component in first_item):
                self.remove(first_item)

        # remove solutions included in one another
        for first_count, first_item in enumerate(contents):
            for second_item in contents[first_count + 1:]:
                try:
                    first_len = len(first_item.includes)
                    second_len = len(second_item.includes)
                    if first_len < second_len:
                        self.remove(second_item)
                    elif first_len > second_len:
                        self.remove(first_item)
                except KeyError:
                    pass

    def remove_dominated(self):
        contents = list(self)
        for first_count, first_item in enumerate(contents):
            for second_item in contents[first_count + 1:]:
                try:
                    if self.compare(first_item, second_item):
                        self.remove(second_item)
                    elif self.compare(second_item, first_item):
                        self.remove(first_item)
                except KeyError:
                    pass

    def json_serializable(self):
        return list(self)
