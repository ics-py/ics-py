import utils

class ParseError(Exception):
    pass

class ContentLine:

    def __eq__(self, other):
        ret = (self.name == other.name 
            and self.params == other.params 
            and self.value == other.value)
        return ret

    __ne__ = lambda self, other: not self.__eq__(other)

    def __init__(self, name, params={}, value=''):
        self.name = name
        self.params = params
        self.value = value

    def __str__(self):
        params_str = ''
        for pname in self.params:
            params_str += ';%s=%s' % (pname, ','.join(self.params[pname]))
        return "%s%s:%s" % (self.name, params_str, self.value)

    def __repr__(self):
        return "<ContentLine '{}' with {} parameters. Value='{}'>".format(self.name, len(self.params), self.value)

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, item, *values):
        self.params[item] = [val for val in values]

    @classmethod
    def parse(klass, line):
        if ':' not in line:
            raise ParseError("No ':' in line '{}'".format(line))
        
        # Separe key and value
        splitted = line.split(':')
        key, value = splitted[0], ':'.join(splitted[1:]).strip()
        
        # Separe name and params
        splitted = key.split(';')
        name, params_strings = splitted[0], splitted[1:]
        
        # Separe key and values for params
        params = {}
        for paramstr in params_strings:
            if '=' not in paramstr:
                raise ParseError("No '=' in line '%s'" % (line))
            splitted = paramstr.split('=')
            pname, pvals = splitted[0], '='.join(splitted[1:])
            params[pname] = pvals.split(',')
        return klass(name, params, value)


class Container(list):
    def __init__(self, name, *items):
        super(Container, self).__init__(items)
        self.name = name

    def __str__(self):
        content_str = '\n'.join(map(str, self))
        if content_str:
            content_str = '\n' + content_str
        return 'BEGIN:%s'%(self.name) + content_str + '\nEND:%s'%(self.name)

    def  __repr__(self):
        return "<Container '{}' with {} elements>".format(self.name, len(self))

    @classmethod
    def parse(klass, name, tokenized_lines):
        items = []
        for line in tokenized_lines:
            if line.name == 'BEGIN':
                items.append(Container.parse(line.value, tokenized_lines))
            elif line.name == 'END':
                if line.value != name:
                    raise ParseError("Expected END:%s, got END:%s"%(name, line.value))
                break
            else:
                items.append(line)
        return klass(name, *items)


def unfold_lines(physical_lines):
    buffer = ""
    remove_space = 0
    for win in utils.window(physical_lines,2):
        if not len(win) == 2:
            yield win[0]
            break
        cur, next = win
        if len(next.strip()) > 0 and next[0] != " ":
            y = buffer + cur[remove_space:]
            remove_space = 0
            buffer = ""
            if len(y) > 0:
                yield y.strip('\n')
        else:
            buffer += cur[remove_space:]
            remove_space = 1
    if len(buffer) > 0:
        yield buffer

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
    return lines_to_container(txt.split('\n'))

if __name__ == "__main__":
    from fixture import cal1
    
    def printTree(elem, lvl=0):
        if isinstance(elem, list) or isinstance(elem, Container):
            if isinstance(elem, Container):
                print '   '*lvl, elem.name
            for sub_elem in elem:
                printTree(sub_elem, lvl+1)
        elif isinstance(elem, ContentLine):
            print '   '*lvl, elem.name, elem.params, elem.value
        else:
            print "Wuuut ?"

    cal = string_to_container(cal1)
    printTree(cal)
