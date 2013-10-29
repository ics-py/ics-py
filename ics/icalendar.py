import parse

#TODO replace len(list())
def get_line(container,name):
    lines = list(filter(lambda x: x.name == name, container))
    if len(lines) != 1:
        raise parse.ParseError('A {} must have one and only one {}'.format(container.name,name))
    return list(lines)[0]

def get_optional_line(container,name):
    lines = list(filter(lambda x: x.name == name, container))
    if len(lines) > 1:
        raise parse.ParseError('A {} must have at most one {}'.format(container.name,name))
    elif len(lines) == 0:
        return None
    else:
        return lines[0]

class Calendar(object):
    """docstring for Calendar"""

    def __init__(self, string=None):
        if string != None:
            if isinstance(string, str):
                container = parse.string_to_container(string)
            else:
                container = parse.lines_to_container(string)

            # TODO : make a better API for multiple calendars
            if len(container) != 1:
                raise NotImplementedError('Multiple calendars in one file are not supported')

            self.populate(container[0])

    @classmethod
    def from_container(klass, container):
        k = klass()
        k.populate(container)
        return k

    def populate(self, container):
        #PRODID
        prodid = get_line(container,'PRODID')
        self.creator = prodid.value
        self.creator_params = prodid.params

        #VERSION
        version = get_line(container,'VERSION')
        self.creator_params = prodid.params
        #TODO : should take care of minver/maxver
        if ';' in version.value:
            _, self.version = version.value.split(';')
        else:
            self.version = version.value

        #CALSCALE
        calscale = get_optional_line(container,'CALSCALE')
        if calscale:
            self.scale = calscale.value
            self.scale_params = calscale.params
        else:
            self.scale = 'georgian'
            self.scale_params = {}
            
        #METHOD
        method = get_optional_line(container,'METHOD')
        if method:
            self.method = method.value
            self.method_params = method.params
        else: 
            self.method = None
            self.method_params = {}

        #VEVENT
        events = filter(lambda x: x.name == 'VEVENT', container)
        self.events = map(lambda x: Event.from_container(x),events)


class Event(object):
    """Docstring for Event """

    def __init__(self):
        pass

    @classmethod
    def from_container(klass, container):
        k = klass()
        
        if container.name != "VEVENT":
            raise parse.ParseError("container isn't an Event")
        k.created = get_optional_line(container, 'CREATED')
        k.begin_date = get_line(container, 'DTSTART')
        # TODO work with timezone
        k.name = get_optional_line(container, 'SUMMARY')

        # TODO : raise if uid not present
        # TODO : add option somwhere to ignore some errors
        k.description = get_optional_line(container,'DESCRIPTION')
        k.uid = None
        k.uid =  get_optional_line(container,'UID')

        return k