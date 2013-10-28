class ParseError(Exception):
    pass


class ContentLine:

    def __eq__(self, other):
        return self.name == other.name and self.params == other.params and self.value == other.value

    __ne__ = lambda a, b: not a.__eq__(b)

    def __init__(self, name, params={}, value=''):
        self.name = name
        self.params = params
        self.value = value

    def __str__(self):
        params_str = ''
        for pname in self.params:
            params_str += ';%s=%s' % (pname, ','.join(self.params[pname]))
        return "%s%s:%s" % (self.name, params_str, self.value)

    __repr__ = __str__

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, item, *values):
        self.params[item] = [val for val in values]

    @classmethod
    def parse(klass, line):
        if ':' not in line:
            raise ParseError("No ':' in line '%s'" % (line))
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

    __repr__ = __str__

class ICSReader:

    def __init__(self, lines):
        if isinstance(lines, str):
            lines = lines.split('\n')
        self.lines = iter(lines)
        self.feof = False
        self.isiter = False

    def __get_line(self):
        try:
            self.next_line = self.lines.next()
            # ignore empty lines
            while not self.next_line:
                self.next_line = self.lines.next()
        except StopIteration:
            self.feof = True
            return False
        return True

    def next(self):
        if self.feof:
            raise StopIteration()
        self.cur_line = self.next_line
        if self.__get_line():
            while self.next_line[0] == ' ':
                self.cur_line = self.cur_line.strip('\n') + self.next_line[1:]
                if not self.__get_line():
                    break
        return ContentLine.parse(self.cur_line)

    def __iter__(self):
        if not self.isiter:
            self.__get_line()
            self.isiter = True
        return self

    def parse(self, block_name=None):
        res = []
        for line in self:
            if line.name == 'BEGIN':
                item = Container(line.value, *self.parse(line.value))
                res.append(item)
            elif line.name == 'END':
                if line.value != block_name:
                    raise ParseError("Expected %s, got %s"%(block_name, line.value))
                return res
            else:
                res.append(line)
        return res

    @classmethod
    def open(klass, filename):
        return klass(open(filename))

if __name__ == "__main__":
    from fixture import cal1
    
    def printTree(cal, lvl=0):
        if isinstance(cal, Container):
            print '   '*lvl, cal.name
            for elem in cal:
                printTree(elem, lvl+1)
        else:
            print '   '*lvl, cal.name, cal.params, cal.value
	
    cal = ICSReader(cal1).parse().pop()
    printTree(cal)
