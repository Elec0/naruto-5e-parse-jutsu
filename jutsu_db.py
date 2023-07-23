from common import DotDict
from jutsu import Jutsu


class JutsuDB(DotDict):
    rank: DotDict
    """ A dictionary of lists of Jutsu, keyed by rank """
    all_keywords: set[str]
    all_jutsu: list[Jutsu]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rank = DotDict()
        self.all_keywords = set()
        self.all_jutsu = []
