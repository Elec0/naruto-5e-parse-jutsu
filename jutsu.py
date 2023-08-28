import re

import yaml

import common
from enums import Rank
from yaml_formatting import Literal, Quoted


class Jutsu:
    _db_entry: dict
    rank: Rank
    name: str
    description: str
    keywords: list[str] = []
    category: str = ""
    # I don't know what the ["consume"]["type"] means. It's always "attribute", but I see nothing related to that in the
    # jutsu itself. So we're ignoring it and treating "amount" as the chakra cost.
    consume: int

    activation: dict
    duration: dict
    target: dict
    range: dict
    uses: dict
    ability: dict
    actionType: str
    damage: dict
    save: dict
    components: dict

    _is_valid: bool = True

    REGEX_KEYWORDS = re.compile(r"(Keyword.*?)(?:<br.*?>|\n|</p>)")
    REGEX_ONE_OFF = re.compile(r"^<p>\s</p>\n")
    CATEGORY_KEYWORDS = ["Ninjutsu", "Genjutsu", "Taijutsu", "Bukijutsu"]
    RELEASE_TYPES = {"yang", "earth", "paper", "poison", "acid", "ink", "yin", "lightning", "water", "wind"}
    # Keywords that are attached to another keyword
    # Example: "Artistic Style": "Style"
    KEYWORD_POSTFIXES = ["Release", "Style", "Branch"]
    NAME_DECORATORS = ["Release", "Style", "Art"]
    IGNORED_RANKS = ["CF_tempEntity"]
    SYSTEM_VARS = ["activation", "duration", "target", "range", "uses", "ability", "actionType", "damage",
                   "save", "components"]

    def __init__(self, db_entry: dict):
        self._db_entry = db_entry
        self._parse_db_entry()

    def for_output(self) -> dict:
        """
        Return a dict that can be dumped to yaml.
        :return:
        """
        return {
            "name": Quoted(self.name),
            "rank": str(self.rank),
            "activation": self.activation,
            "keywords": self.keywords,
            "description": Literal(self.description),
            "category": self.category,
            "duration": self.duration,
            "target": self.target,
            "range": self.range,
            "uses": self.uses,
            "consume": self.consume,
            "ability": self.ability,
            "action_type": self.actionType,
            "damage": self.damage,
            "save": self.save,
            "components": self.components
        }

    def _parse_db_entry(self):
        db = self._db_entry

        self.name = db["name"]

        self._parse_rank()
        self.description = db["system"]["description"]["value"]
        self.consume = db["system"]["consume"]["amount"]

        if self.description is not None and self.description != "":
            self._pre_cleanup_description()
            self._keywords_parse()

        for var in self.SYSTEM_VARS:
            if var in db["system"]:
                setattr(self, var, db["system"][var])

        self._cleanup_description()
        self._set_category()
        self._decorate_name()

    def name_as_path(self) -> str:
        """
        The YAML name of the jutsu does not have to match the filename.
        :return: Valid path name of the name of the jutsu
        """
        pname = self.name.replace(":", "-")
        pname = pname.replace("/", "-")
        replace_chars = ["(", ")", "[", "]", " ", ",", ".", "'", '"', "!", "?"]
        # Use regex to delete all instances of the characters in replace_chars
        return re.sub(rf"[{''.join(replace_chars)}]", "", pname)

    def _decorate_name(self):
        """
        Do things like add ":" after "Water/Wind/Swift Release" in the name.
        :return:
        """
        if m := re.match(rf"(^\w+ ({'|'.join(self.NAME_DECORATORS)}))", self.name, re.IGNORECASE):
            release = " ".join(word.capitalize() for word in m.group(0).split(" "))
            self.name = f"{release}: {self.name[len(m.group(0)) + 1:]}"

    def _pre_cleanup_description(self):
        """
        Do specific cleanup before keywords are parsed.
        """
        # One-off fix for "Water Escape [D]"

        if re.match(self.REGEX_ONE_OFF, self.description):
            self.description = re.sub(self.REGEX_ONE_OFF, "", self.description)

        # Unicode exists in some text, and when reading it in python it's escaped, so we need to unescape it.
        self.description = bytes(self.description, "unicode-escape").decode("unicode-escape")

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
        # Replace bullet point characters with dashes
        description = re.sub(r"•", "-", description)
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
        return yaml.dump(self.for_output(), default_flow_style=False, allow_unicode=True)

    def to_obsidian(self) -> str:
        res = ""
        res += "---\n"
        res += yaml.dump(self.for_output(), default_flow_style=False, allow_unicode=True)
        res += "---\n"
        render_block = ("```dataviewjs\n"
                        "const {RenderJutsu} = customJS\n"
                        "RenderJutsu.renderBlock(dv, dv.current())\n"
                        "```\n")
        res += render_block
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
