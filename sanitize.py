import re

from .utils import TextUtils


class Sanitize(object):

    @staticmethod
    def text(value: str, allow_dot: bool = False, allow_space: bool = True, allow_parentheses: bool = True,
             remove_special_characters: bool = True, to_upper: bool = False, to_lower: bool = False,
             max_size: int = 255) -> str:
        allow = "\w"
        if allow_dot:
            allow += "."
        if allow_space:
            allow += " "
        if allow_parentheses:
            allow += "()"
        value = re.sub(r"[^" + allow + "]", "_", value)
        value = re.sub(r"_+", "_", value.strip("_")).strip()
        if to_upper:
            value = value.upper()
        elif to_lower:
            value = value.lower()
        if remove_special_characters:
            value = TextUtils.remove_special_characters(value)
        return value[:max_size]

    @staticmethod
    def url(url: str) -> str:
        return re.sub(r"([^:])//", "\\g<1>/", url)
