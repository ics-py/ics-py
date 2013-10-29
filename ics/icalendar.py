import parse

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
        creators = filter(lambda x: x.name == 'PRODID', container)
        if len(creators) != 1:
            raise parse.ParseError('A calendar must have one and only one PRODID')
        prodid = creators[0]
        self.creator = prodid.value
        self.creator_params = prodid.params

        #VERSION
        version = filter(lambda x: x.name == 'VERSION', container)
        if len(version) != 1:
            raise parse.ParseError('A calendar must have one and only one VERSION')
        version = version[0]
        self.creator_params = prodid.params
        #TODO : should take care of minver/maxver
        if ';' in version.value:
            _, self.version = version.value.split(';')
        else:
            self.version = version.value
        

        #CALSCALE
        calscale = filter(lambda x: x.name == 'CALSCALE', container)
        if len(calscale) > 1:
            raise parse.ParseError('A calendar must have at most one CALSCALE')

        self.scale = 'georgian'
        self.scale_params = {}
        if len(calscale) == 1:
            self.scale = calscale[0].value
            self.scale_params[0].update(calscale.params)

        #METHOD
        method = filter(lambda x: x.name == 'METHOD', container)
        if len(method) > 1:
            raise parse.ParseError('A calendar must have at most one METHOD')

        self.method = None
        self.method_params = {}
        if len(method) == 1:
            self.method = method[0].value
            self.method_params[0].update(method.params)

        #VEVENT
        events = filter(lambda x: x.name == 'VEVENT', container)
        self.events = map(lambda x: Event.from_container(x),events)


