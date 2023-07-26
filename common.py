import re
from collections import UserDict
from typing import Any


def remove_html_tags(text: str) -> str:
    """
    Remove html tags from a string.
    Keep <br> and <br/> tags, since they are used for line breaks.
    :param text:
    :return:
    """
    # Remove all tags except <br> and <br/>
    return re.sub(r"(?!<br.*?>)<.*?>", "", text)


class JutsuRankException(Exception):
    """Raised when a jutsu rank is not valid."""

    def __init__(self, message):
        super().__init__(message)
