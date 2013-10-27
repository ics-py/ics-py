class ParseError(Exception):
	pass

class ContentLine:
	def __eq__(self, other):
		return self.name==other.name and self.params == other.params and self.value == other.value
	
	
	__ne__ = lambda a,b: not a.__eq__(b)
	
	def __init__(self, name, params={}, value=''):
		self.name = name
		self.params = params
		self.value = value
	
	
	def __str__(self):
		params_str = ''
		for pname in self.params:
			params_str += ';%s=%s'%(pname, ','.join(self.params[pname]))
		return "%s%s:%s"%(self.name, params_str, self.value)
	
	__repr__ = __str__
	
	@classmethod
	def parse(klass, line):
		if ':' not in line:
			raise ParseError("No ':' in line '%s'"%(line))
		#Separe key and value
		splitted = line.split(':')
		key, value = splitted[0], ':'.join(splitted[1:]).strip()
		#Separe name and params
		splitted = key.split(';')
		name, params_strings = splitted[0], splitted[1:]
		#Separe key and values for params
		params = {}
		for paramstr in params_strings:
			if '=' not in paramstr:
				raise ParseError("No '=' in line '%s'"%(line))
			splitted = paramstr.split('=')
			pname, pvals = splitted[0], '='.join(splitted[1:])
			params[pname] = pvals.split(',')
		return klass(name, params, value)
	
