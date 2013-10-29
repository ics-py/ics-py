import parse

def make_calendars(l):
    if len(l) > 1:
        raise NotImplementedError('Multiple calendars in one file are not supported')
    if len(l) == 0:
        return []
    return Calendar(l[0])

class Calendar(object):
    """docstring for Calendar"""

    def __init__(self, string=None):
        if string != None:
            if isinstance(string, str):
                container = parse.string_to_container(string)
            else:
                container = parse.lines_to_container(string)

            # TODO : make a better API for multiple calendars
            if len(container) > 1:
                raise NotImplementedError('Multiple calendars in one file are not supported')
            if len(container) == 0:
                return None
            self.populate(container[0])

    def populate(self, container):

        creators = filter(lambda x: x.name == 'PRODID', container)
        if len(creators) != 1:
            raise parse.ParseError('A calendar must have one and only one PRODID')
        self.creator = creators[0].value

