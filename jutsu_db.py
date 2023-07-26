from enums import Rank
from jutsu import Jutsu


class JutsuDB:
    rank: dict[Rank, list[Jutsu]]
    """ A dictionary of lists of Jutsu, keyed by rank """
    name: dict[str, Jutsu]
    """ A dictionary of lists of Jutsu, keyed by name """
    all_keywords: set[str]
    all_jutsu: list[Jutsu]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rank = {}
        self.all_keywords = set()
        self.all_jutsu = []
        self.name: dict[str, Jutsu] = {}

    def add(self, jutsu: Jutsu):
        if jutsu.rank.name not in self.rank.keys():
            self.rank[jutsu.rank] = []

        # There are some duplicate jutsu names, for casting at different ranks
        # We're going to skip the duplicates and use the one with the lowest rank
        if jutsu.name in self.name.keys():
            # If the new jutsu is a lower rank, replace the old one
            old_jutsu = self.name[jutsu.name]

            if jutsu.rank > old_jutsu.rank:
                print(f"Replacing {old_jutsu.name} [{old_jutsu.rank}] with "
                      f"{jutsu.name} [{jutsu.rank}]")
                self.rank[old_jutsu.rank].remove(old_jutsu)
                self.all_jutsu.remove(old_jutsu)

        self.name[jutsu.name] = jutsu
        self.rank[jutsu.rank].append(jutsu)
        self.all_jutsu.append(jutsu)
        # Insert jutsu keywords into the set
        self.all_keywords.update(jutsu.keywords)

    def get(self, name: str) -> Jutsu:
        return self.name[name]

    def has(self, name: str) -> bool:
        return name in self.name.keys()
