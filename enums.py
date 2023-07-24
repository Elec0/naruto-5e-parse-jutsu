from enum import Enum
from functools import total_ordering


@total_ordering
class Rank(Enum):
    E, D, C, B, A, S = range(6)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other

        return self.value == other.value

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.value < other.value

    def __hash__(self):
        return hash(self.value)
