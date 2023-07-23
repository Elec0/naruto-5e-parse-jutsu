import re
from typing import Any


def remove_html_tags(text: str) -> str:
    return re.sub('<[^<]+?>', '', text)


class DotDict(dict):
    """
    A dictionary supporting dot notation.
    """

    def __getattr__(self, key: str) -> Any:
        try:
            return self.__getitem__(key)
        except KeyError as ex:
            raise AttributeError(key) from ex

    # __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __dir__(self):
        return self.keys()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = DotDict(v)

    def lookup(self, dotkey):
        """
        Lookup value in a nested structure with a single key, e.g. "a.b.c"
        """
        path = list(reversed(dotkey.split(".")))
        v = self
        while path:
            key = path.pop()
            if isinstance(v, dict):
                v = v[key]
            elif isinstance(v, list):
                v = v[int(key)]
            else:
                raise KeyError(key)
        return v
