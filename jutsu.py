import re

import yaml

import common
from enums import Rank


class Jutsu:
    _db_entry: dict
    rank: Rank
    name: str
    description: str
    activation: dict
    keywords: list[str] = []
    category: str = ""
    _is_valid: bool = True

    REGEX_KEYWORDS = re.compile(r"(Keyword.*?)(?:<br.*?>|\n|</p>)")
    REGEX_ONE_OFF = re.compile(r"^<p>\s</p>\n")
    CATEGORY_KEYWORDS = ["Ninjutsu", "Genjutsu", "Taijutsu", "Bukijutsu"]
    RELEASE_TYPES = {"yang", "earth", "paper", "poison", "acid", "ink", "yin", "lightning", "water", "wind"}
    # Keywords that are attached to another keyword
    # Example: "Artistic Style": "Style"
    KEYWORD_POSTFIXES = ["Release", "Style", "Branch"]
    IGNORED_RANKS = ["CF_tempEntity"]

    def __init__(self, db_entry: dict):
        self._db_entry = db_entry
        self._parse_db_entry()

    def for_output(self) -> dict:
        """
        Return a dict that can be dumped to yaml.
        :return:
        """
        return {
            "name": self.name,
            "rank": str(self.rank),
            "activation": self.activation,
            "keywords": self.keywords,
            "description": self.description
        }

    def _parse_db_entry(self):
        db = self._db_entry

        self.name = db["name"]
        self._cleanup_name()

        self._parse_rank()
        self.description = db["system"]["description"]["value"]

        if self.description is not None and self.description != "":
            self._pre_cleanup_description()
            self._keywords_parse()

        self.activation = db["system"]["activation"]

        self._cleanup_description()
        self._set_category()

    def _cleanup_name(self):
        """
        Format names such that they are valid Path names.
        """
        self.name = self.name.replace(":", "-")
        self.name = self.name.replace("/", "-")
        replace_chars = ["(", ")", "[", "]", " ", ",", ".", "'", '"', "!", "?"]
        # Use regex to delete all instances of the characters in replace_chars
        self.name = re.sub(rf"[{''.join(replace_chars)}]", "", self.name)

    def _pre_cleanup_description(self):
        """
        Do specific cleanup before keywords are parsed.
        """
        # One-off fix for "Water Escape [D]"

        if re.match(self.REGEX_ONE_OFF, self.description):
            self.description = re.sub(self.REGEX_ONE_OFF, "", self.description)

    def _cleanup_description(self):
        """
        Remove html tags from description.
        Must be done after keyword parsing.
        :return:
        """
        description = self.description
        # Remove ONLY the 1st <p> to </p> block, using regex replace
        # we should not remove all the blocks, since some might not be keywords groups
        description = re.sub(rf"<p>.*?</p>", "", description, count=1)
        description = common.remove_html_tags(description)
        description = description.strip()

        self.description = description

    def _keywords_get_all(self):
        description = self.description
        if description == "" or description is None:
            return

        val = re.search(r"(Keywords?:|<p>).*?(?:<br.*?>|\n|</p>)", description,
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
        """
        throws KeyError If the rank is not found in the Rank enum
        :return:
        """
        str_rank = self.name.split("[")[1].split("]")[0].strip()
        try:
            self.rank = Rank[str_rank]
        except KeyError:  # This jutsu should be excluded
            self._is_valid = False
            raise common.JutsuRankException(f"Invalid rank: {str_rank}")
        # Remove rank from name
        self.name = self.name.split("[")[0].strip()

    def _set_category(self):
        """
        Set the category based on if Ninjutsu/Genjutsu/Taijutsu/Bukijutsu is in the keywords.
        """
        for keyword in self.keywords:
            if keyword in Jutsu.CATEGORY_KEYWORDS:
                self.category = keyword
                return
        # If we fall through, check if it's Hijutsu and use that (Falling Heaven: Focus & Serpent Adaptation)
        if "Hijutsu" in self.keywords:
            self.category = "Hijutsu"

    def to_yaml(self) -> str:
        return yaml.dump(self.for_output(), default_flow_style=False)

    def to_obsidian(self) -> str:
        res = ""
        res += "```\n"
        res += yaml.dump(self.for_output(), default_flow_style=False)
        res += "```"
        return res

    def __str__(self):
        return f"{self.name} ({self.rank}): Cast time: {self.activation}, Keywords: {', '.join(self.keywords)}, " \
               f"{self.description}"

    def __repr__(self):
        return f'Jutsu("{self.name}", Rank: "{self.rank}", ' \
               f'Cast time: "{self.activation["cost"]} {self.activation["type"]}", ' \
               f'Keywords: {self.keywords})'

    @property
    def is_valid(self):
        return self._is_valid
