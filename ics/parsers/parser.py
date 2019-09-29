from typing import NamedTuple, Optional, List, Tuple, Dict, Callable
from ics.parse import ContentLine


class ParserOption(NamedTuple):
    required: bool = False
    multiple: bool = False
    default: Optional[List[ContentLine]] = None


class Parser:
    @classmethod
    def get_extractors(cls) -> Dict[str, Tuple[Callable, ParserOption]]:
        methods = dir(cls)
        return {
            m.__name__.split("_", 1)[1].upper(): (m, getattr(m, 'options', ParserOption()))
            for m in methods
            if m.__name__.startswith('parse_')
        }


def option(
    required: bool = False,
    multiple: bool = False,
    default: Optional[List[ContentLine]] = None
) -> Callable:
    def decorator(fn):
        fn.options = ParserOption(required, multiple, default)
        return fn
    return decorator
