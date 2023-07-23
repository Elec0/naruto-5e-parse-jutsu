import json
import re
from collections import OrderedDict

import common


# "name"
# "system": {
#   "description": { "value" }
#   "activation": {
#        "type", "cost", "condition"
#        type is things like: "action", "bonus", "reaction", "minute/hour/day"
#        cost is usually "1", but can be "0", or other numbers for minutes/hours/days
#        condition is things like: "full round action, when you would take damage, must be in a stance"
# }
# }

class Jutsu:
    _db_entry: dict
    rank: str
    name: str
    description: str
    activation: dict
    keywords: list[str] = []

    REGEX_KEYWORDS = re.compile(r"(Keyword.*?)(?:<br.*?>|\n|</p>)")
    RELEASE_TYPES = {"mist", "storm", "plasma", "steel", "yang", "dust", "ash", "earth", "lava", "magma", "swift",
                     "corrosion", "paper", "vapor", "explosion", "poison", "acid", "miasma", "wood", "ink", "steam",
                     "yin", "sand", "blaze", "fire", "shadow", "magnet", "salt", "mud", "ice", "lightning", "smoke",
                     "water", "crystal", "bubble", "wind", "scorch", "boil", "sound", "snow", "medical"}
    # Keywords that are attached to another keyword
    # Example: "Artistic Style": "Style"
    KEYWORD_POSTFIXES = ["Release", "Style", "Branch"]

    def __init__(self, db_entry: dict):
        self._db_entry = db_entry
        self._parse_db_entry()

    def _parse_db_entry(self):
        db = self._db_entry

        self.name = db["name"]
        self._parse_rank()
        self.description = db["system"]["description"]["value"]

        if self.description is not None and self.description != "":
            self._keywords_parse()

        self.activation = db["system"]["activation"]

        self._cleanup_description()

    def _cleanup_description(self):
        """
        Remove html tags from description.
        Must be done after keyword parsing.
        :return:
        """
        description = self.description
        # Remove ONLY the 1st <p> to </p> block, using regex replace
        regex_para = re.compile(r"<p>.*?</p>")
        description = regex_para.sub("", description, count=1)
        description = common.remove_html_tags(description)

        self.description = description

    def _keywords_get_all(self):
        description = self.description
        if description == "" or description is None:
            return

        val = re.search(r"(Keywords?:).*?(?:<br.*?>|\n|</p>)", description,
                        re.RegexFlag.MULTILINE | re.RegexFlag.DOTALL)
        if val is None:
            return

        if len(val.groups()) > 1:
            print("!!! More than 1 group found !!!")

        if len(val.group(0)) > 100:
            print("- group too long, skipping")
            return

        return val.group(0)

    def _keywords_parse(self):
        """
        Parse keywords from description.

        The value is in description, at the beginning, always the same:

        .. code-block::

            <p>Keywords: Genjutsu, Visual, Unaware</p>\\n<p>

        Ok, so it turns out it's *not* always the same.
        We want to extract keywords after the first colon, and before the </p> tag.
        :return:
        """
        all_keywords = self._keywords_get_all()
        if all_keywords is None:
            return
        # Remove the parts we don't want: "Keywords:", "<p>", "</p>", "\n", "<br.*?>", "release"
        keywords_clean = re.sub(r"(Keywords?:|<p>|</p>|\n|<br.*?>|[Rr]elease|\.)", "", all_keywords,
                                flags=re.RegexFlag.MULTILINE)

        # Split on comma, and strip whitespace
        keywords = [k.strip() for k in keywords_clean.split(",")]

        # Remove empty keywords, in case they exist
        self.keywords = [k for k in keywords if k != ""]
        self.keywords = self._keywords_refine()

    def _keywords_refine(self):
        """
        Remove duplicates in the form of "Keyword1 Keyword2", where "Keyword1" and "Keyword2" are present in the full
        list of keywords.
        Handle "Bukijutsu Earth Release"
        """
        # Don't modify the list we're iterating over
        final_keywords = self.keywords.copy()
        for k in self.keywords:
            words = k.split(" ")
            add_last = None

            # Do this first, if it's true then the second loop never needs to run
            if k.lower() in Jutsu.RELEASE_TYPES:
                final_keywords.remove(k)
                final_keywords.append(f"{k} Release")
                continue

            if len(words) == 1:
                continue

            # If len(words) == 2, it might be legit ("Earth Release"), but also it might not be ("Bukijutsu Earth")
            # We need to check each element + the next one (if it exists) to see if it's a valid keyword
            for prev, curr in zip(words, words[1:]):
                add_last = None
                final_keywords.remove(k)

                # If the current word is a valid postfix, these 2 are valid
                if curr in Jutsu.KEYWORD_POSTFIXES:
                    final_keywords.append(f"{prev} {curr}")
                    continue
                # If the previous word is a valid postfix, it--and it's predecessor--have already been added to
                # final_keywords, so we can discard them.
                # Now we're at a strange spot where the current word is probably valid, but there may or may not be a
                # next word. If there is, we need to check it (already handled by the next loop iteration).
                # But if there isn't a next word, we need to add the current word to final_keywords.
                if prev in Jutsu.KEYWORD_POSTFIXES:
                    # Let's handle that by saving the word to a variable and clear it the next iteration.
                    # Then, if there isn't a next iteration, we add the current word to final_keywords.
                    add_last = curr
                    continue

            if add_last is not None:
                final_keywords.append(add_last)

        return final_keywords

    def _parse_rank(self):
        self.rank = self.name.split("[")[1].split("]")[0].strip()
        # Remove rank from name
        self.name = self.name.split("[")[0].strip()

    def __str__(self):
        return f"{self.name} ({self.rank}): {self.activation}, Keywords: {', '.join(self.keywords)}, {self.description}"


jutsu_keywords = set()


def run():
    with open("jutsu.db", encoding="utf-8") as f:
        db = f.readlines()

    jutsu_rank = {}
    jutsu_list = []

    for line in db:
        line_json = json.loads(line)
        jutsu = Jutsu(line_json)

        if jutsu.rank not in jutsu_rank:
            jutsu_rank[jutsu.rank] = []

        jutsu_rank[jutsu.rank].append(jutsu)
        jutsu_list.append(jutsu)
        # Insert jutsu keywords into the set
        jutsu_keywords.update(jutsu.keywords)

    for rank in jutsu_rank.keys():
        print(f"{rank}-Rank Jutsu: {len(jutsu_rank[rank])}")

    print(f"Total Jutsu: {len(jutsu_list)}")
    print()

    # All water jutsu are tagged with "Water Release"
    # Fire is missing 'release' from some

    keyword_set = OrderedDict()
    water_jutsu = []
    for j in jutsu_list:
        for k in j.keywords:
            keyword_set[k] = 1
            if "fire" in k.lower():
                water_jutsu.append(j)
                break

    print(f"Keywords: {' | '.join(keyword_set.keys())}")
    print(f"Filtered Jutsu: {len(water_jutsu)}")


if __name__ == "__main__":
    run()
