import collections
from pathlib import Path

import tatsu

CRLF = '\r\n'

grammar_path = Path(__file__).parent.joinpath('contentline.ebnf')

with open(grammar_path) as fd:
    GRAMMAR = tatsu.compile(fd.read())


class ParseError(Exception):
    pass


class ContentLine:
    """ represents one property of calendar content

    name:   the name of the property (uppercased for consistency and
            easier comparison)
    params: a dict of the parameters
    value:  its value
    """

    def __eq__(self, other):
        ret = (self.name == other.name and
               self.params == other.params and
               self.value == other.value)
        return ret

    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, name, params={}, value=''):
        self.name = name.upper()
        self.params = params
        self.value = value

    def __str__(self):
        params_str = ''
        for pname in self.params:
            params_str += ';{}={}'.format(pname, ','.join(self.params[pname]))
        return "{}{}:{}".format(self.name, params_str, self.value)

    def __repr__(self):
        return "<ContentLine '{}' with {} parameter{}. Value='{}'>" \
            .format(
                self.name,
                len(self.params),
                "s" if len(self.params) > 1 else "",
                self.value,
            )

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, item, *values):
        self.params[item] = [val for val in values]

    @classmethod
    def parse(cls, line):
        try:
            ast = GRAMMAR.parse(line + CRLF)
        except tatsu.exceptions.FailedToken:
            raise ParseError()

        name = ''.join(ast['name'])
        value = ''.join(ast['value'])
        params = {}
        for param_ast in ast.get('params', []):
            param_name = ''.join(param_ast["name"])
            param_values = [''.join(x) for x in param_ast["values_"]]
            params[param_name] = param_values
        return cls(name, params, value)

    def clone(self):
        # dict(self.params) -> Make a copy of the dict
        return self.__class__(self.name, dict(self.params), self.value)


class Container(list):
    """ represents one calendar object.
    Contains a list of ContentLines or Containers.

    name: the name of the object (VCALENDAR, VEVENT etc.)
    """

    def __init__(self, name, *items):
        super(Container, self).__init__(items)
        self.name = name

    def __str__(self):
        name = self.name
        ret = ['BEGIN:' + name]
        for line in self:
            ret.append(str(line))
        ret.append('END:' + name)
        return CRLF.join(ret)

    def __repr__(self):
        return "<Container '{}' with {} element{}>" \
            .format(self.name, len(self), "s" if len(self) > 1 else "")

    @classmethod
    def parse(cls, name, tokenized_lines):
        items = []
        for line in tokenized_lines:
            if line.name == 'BEGIN':
                items.append(Container.parse(line.value, tokenized_lines))
            elif line.name == 'END':
                if line.value != name:
                    raise ParseError(
                        "Expected END:{}, got END:{}".format(name, line.value))
                break
            else:
                items.append(line)
        return cls(name, *items)

    def clone(self):
        c = self.__class__(self.name)
        for elem in self:
            c.append(elem.clone())
        return c


def unfold_lines(physical_lines):
    if not isinstance(physical_lines, collections.abc.Iterable):
        raise ParseError('Parameter `physical_lines` must be an iterable')
    current_line = ''
    for line in physical_lines:
        if len(line.strip()) == 0:
            continue
        elif not current_line:
            current_line = line.strip('\r')
        elif line[0] in (' ', '\t'):
            # TODO : remove more spaces if needed
            current_line += line[1:].strip('\r')
        else:
            yield(current_line)
            current_line = line.strip('\r')
    if current_line:
        yield(current_line)


def tokenize_line(unfolded_lines):
    for line in unfolded_lines:
        yield ContentLine.parse(line)


def parse(tokenized_lines, block_name=None):
    res = []
    for line in tokenized_lines:
        if line.name == 'BEGIN':
            res.append(Container.parse(line.value, tokenized_lines))
        else:
            res.append(line)
    return res


def lines_to_container(lines):
    return parse(tokenize_line(unfold_lines(lines)))


def string_to_container(txt):
    return lines_to_container(txt.splitlines())


def interpret_ast(ast):
    name = ''.join(ast['name'])
    value = ''.join(ast['value'])
    params = {}
    for param_ast in ast.get('params', []):
        param_name = ''.join(param_ast["name"])
        param_values = [''.join(x) for x in param_ast["values_"]]
        params[param_name] = param_values
    return ContentLine(name, params, value)


def calendar_string_to_containers(string):
    if not isinstance(string, str):
        raise TypeError("Expecting a string")
    return string_to_container(string)
