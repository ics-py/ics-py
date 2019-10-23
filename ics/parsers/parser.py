from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

from ics.grammar.parse import ContentLine


class ParserOption(NamedTuple):
    required: bool = False
    multiple: bool = False
    default: Optional[List[ContentLine]] = None


class Parser:
    @classmethod
    def get_parsers(cls) -> Dict[str, Tuple[Callable, ParserOption]]:
        methods = [
            (method_name, getattr(cls, method_name))
            for method_name in dir(cls)
            if callable(getattr(cls, method_name))
        ]
        parsers = [
            (method_name, method_callable)
            for (method_name, method_callable) in methods
            if method_name.startswith("parse_")
        ]
        return {
            method_name.split("_", 1)[1]
            .upper()
            .replace("_", "-"): (
                method_callable,
                getattr(method_callable, "options", ParserOption()),
            )
            for (method_name, method_callable) in parsers
        }


def option(
    required: bool = False,
    multiple: bool = False,
    default: Optional[List[ContentLine]] = None,
) -> Callable:
    def decorator(fn):
        fn.options = ParserOption(required, multiple, default)
        return fn

    return decorator
