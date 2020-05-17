from typing import Iterator, Union, Tuple

import attr
import importlib_resources  # type: ignore
import tatsu  # type: ignore
import tatsu.exceptions  # type: ignore
import tatsu.grammars  # type: ignore
from ics.contentline.common import *

GRAMMAR = tatsu.compile(importlib_resources.read_text(__package__, "grammar.ebnf"))


@attr.s
class TatsuParser(Parser):
    grammar = attr.ib()

    def string_to_contentlines(self, txt: str) -> Iterator[ContentLine]:
        try:
            ast = self.grammar.parse(txt, rule_name='full')
        except tatsu.exceptions.FailedToken as e:
            raise ParseError(str(e))
        for line in ast:
            yield self.interpret_ast(line)

    def lines_to_contentlines(self, lines: Iterator[Union[Tuple[int, str], str]]) -> Iterator[ContentLine]:
        for line in lines:
            nr = -1
            filename = None
            if not isinstance(line, str):
                nr, line = line
                filename = "Line %s" % nr
            try:
                ast = self.grammar.parse(line, rule_name='start', filename=filename)
            except tatsu.exceptions.FailedToken as e:
                raise ParseError(str(e), nr, line=line)
            yield self.interpret_ast(ast)

    def interpret_ast(self, ast):
        cl = ContentLine(
            name=''.join(ast['name']),
            value=''.join(ast['value']))
        for param_ast in ast.get('params', []):
            param_name = ''.join(param_ast["name"])
            cl.params[param_name] = []
            for param_value_ast in param_ast["values"]:
                val = self.unescape_param(param_value_ast["value"])
                if param_value_ast["quoted"] == "true":
                    val = QuotedParamValue(val)
                cl.params[param_name].append(val)
        return cl
