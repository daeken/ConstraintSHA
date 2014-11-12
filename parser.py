import re, sys
from pprint import pprint
from sets import Set

def matcher(regexp):
	regexp = re.compile(regexp)

	def sub(data):
		match = regexp.match(data)
		if match == None:
			return None
		return match.group(0)
	return sub

hex = matcher(r'0x[0-9a-fA-F]+')
number = matcher(r'-?[0-9]+')
name = matcher(r'[a-zA-Z\-_+*/<>\[\]=\^&|%~!][a-zA-Z0-9\-_+*/<>\[\]=\^&|%~!]*')

def clean(code):
	code = re.sub(r';.*', '', code)
	code = re.sub(r'\s+', ' ', code)
	return code

def parseAtom(code):
	code = code.lstrip()
	if code[0] == '(':
		code = code[1:].lstrip()
		atom = []
		while code[0] != ')':
			val, code = parseAtom(code)
			code = code.lstrip()
			atom.append(val)
		return atom, code[1:]
	if hex(code):
		val = hex(code)
		return int(val[2:], 16), code[len(val):]
	elif number(code):
		val = number(code)
		return int(val), code[len(val):]
	elif name(code):
		val = name(code)
		return val, code[len(val):]
	else:
		print 'bailing!'
		print code
		sys.exit(1)

def join(arr):
	return reduce(lambda a, b: a + b, arr)

def unroll(code, replace):
	if not isinstance(code, list):
		if code in replace:
			return [replace[code]]
		else:
			return [code]

	if code[0] == 'for':
		var, start, end = code[1:4]
		block = code[4:]
		out = []
		for i in xrange(start, end):
			replace[var] = i
			out += join(map(lambda x: unroll(x, replace), block))
		return out
	else:
		code = join(map(lambda x: unroll(x, replace), code))
		return [code]

def rewrite_constant(code):
	if not isinstance(code, list):
		return code

	constant = lambda x: False not in [isinstance(elem, int) or isinstance(elem, long) for elem in x]
	code = list(map(rewrite_constant, code))
	func, rest = code[0], code[1:]
	if not constant(rest):
		return code

	if func == '+':
		return reduce(lambda a, b: a + b, rest) & 0xFFFFFFFF
	elif func == '-':
		return reduce(lambda a, b: a - b, rest) & 0xFFFFFFFF
	elif func == '^':
		return reduce(lambda a, b: a ^ b, rest)
	elif func == '|':
		return reduce(lambda a, b: a | b, rest)
	elif func == '&':
		return reduce(lambda a, b: a & b, rest)
	elif func == '~':
		return rest[0] ^ 0xFFFFFFFF
	elif func == '>>':
		return reduce(lambda a, b: a >> b, rest)
	elif func == '<<':
		return reduce(lambda a, b: a << b, rest) & 0xFFFFFFFF
	else:
		return code

def wrap_ssa(code, vars):
	return join(ssa(code, vars))

def ssa(code, vars):
	def rename(var):
		if var in vars:
			return '%s_%i' % (var, vars[var])
		else:
			return var
	if not isinstance(code, list):
		if code in vars:
			return [rename(code)]
		else:
			return [code]

	if code[0] == '=':
		name, val = code[1:]

		if isinstance(val, list) and val[0] == 'list':
			out = []
			for i, elem in enumerate(val[1:]):
				ename = '%s_%i' % (name, i)
				if ename not in vars:
					vars[ename] = 0
				else:
					vars[ename] += 1
				out.append(['=', rename(ename), wrap_ssa(elem, vars)])
			return out
		else:
			if name not in vars:
				vars[name] = 0
			else:
				vars[name] += 1
			return [['=', rename(name), wrap_ssa(val, vars)]]
	elif code[0] == 'set':
		name, index, val = code[1:]
		assert isinstance(index, int) or isinstance(index, long)
		name = '%s_%i' % (name, index)
		if name not in vars:
			vars[name] = 0
		else:
			vars[name] += 1
		return [['=', rename(name), wrap_ssa(val, vars)]]
	elif code[0] == 'get':
		name, index = code[1:]
		assert isinstance(index, int) or isinstance(index, long)
		name = '%s_%i' % (name, index)
		return [rename(name)]
	else:
		code = join(map(lambda x: ssa(x, vars), code))
		return [code]

def find_uses(code, used):
	if not isinstance(code, list):
		if isinstance(code, str):
			used.add(code)
		else:
			return []

	func, rest = code[0], code[1:]
	for elem in rest[1 if func == '=' else 0:]:
		find_uses(elem, used)

def remove_dead(code, used, vars):
	assert code[0] == 'cdef'

	out = ['cdef']

	for elem in code[1:]:
		assert isinstance(elem, list)
		if elem[0] == '=':
			name = elem[1]
			base, num = name.rsplit('_', 1)
			if name not in used and vars[base] != int(num):
				pass
			else:
				out.append(elem)
		else:
			out.append(elem)

	return out

def parse(code):
	code = clean(code)

	atom, rest = parseAtom(code)
	assert rest.strip() == ''

	atom = join(unroll(atom, {}))
	atom = rewrite_constant(atom)
	vars = {}
	atom = join(ssa(atom, vars))
	used = Set()
	find_uses(atom, used)
	atom = remove_dead(atom, used, vars)
	#pprint(atom)

	return atom

if __name__=='__main__':
	parse(file(sys.argv[1], 'r').read())
