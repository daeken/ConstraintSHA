from parser import parse
import sys

def gfunc(name):
	def sub(func):
		gfuncs[name] = func
		return func
	return sub
gfuncs = {}

@gfunc('list')
def _list(*elems):
	return list(elems)

gfunc('len')(len)

@gfunc('print')
def _print(*elems):
	for i, elem in enumerate(elems):
		if i == len(elems) - 1:
			print elem
		else:
			print elem, 

@gfunc('print-hex')
def _printhex(*elems):
	if len(elems) == 1 and isinstance(elems[0], list):
		print ' '.join('%x' % elem for elem in elems[0])
		return
	for i, elem in enumerate(elems):
		if i == len(elems) - 1:
			print '0x%x' % elem
		else:
			print '0x%x' % elem, 

@gfunc('>>')
def rshift(left, right):
	return wrapmod(left >> right)

@gfunc('<<')
def lshift(left, right):
	return wrapmod(left << right)

@gfunc('>>>')
def rroll(left, right):
	return wrapmod((left >> right) | wrapmod(left << (32 - right)))

@gfunc('<<<')
def lroll(left, right):
	return wrapmod(wrapmod(left << right) | (left >> (32 - right)))

@gfunc('^')
def xor(*elems):
	return reduce(lambda a, b: a ^ b, elems)

@gfunc('&')
def _and(*elems):
	return reduce(lambda a, b: a & b, elems)

@gfunc('-')
def _sub(*elems):
	return wrapmod(reduce(lambda a, b: a - b, elems))

@gfunc('+')
def _add(*elems):
	return wrapmod(reduce(lambda a, b: a + b, elems))

@gfunc('~')
def _anot(elem):
	if int_size == 0:
		return ~elem

	return elem ^ ((1 << int_size) - 1)

@gfunc('==')
def _eq(left, right):
	return left == right

@gfunc('int-size')
def _int_size(size):
	global int_size
	int_size = size

@gfunc('get')
def _get(list, i):
	return list[i]

@gfunc('set')
def _set(list, i, val):
	list[i] = val
	return val

def wrapmod(val):
	if int_size == 0:
		return val

	if int_size == 32:
		return val & 0xFFFFFFFF

int_size = 0

class Runner(object):
	def __init__(self, code, **external_defaults):
		self.code = parse(code)
		assert self.code[0] == 'cdef'

		self.variables = {}
		for name, val in external_defaults.items():
			if isinstance(val, list):
				for i, val in enumerate(val):
					self.variables['%s_%i' % (name, i)] = val
			else:
				self.variables[name] = val

		for atom in self.code[1:]:
			self.execute(atom)

	def execute(self, atom):
		try:
			if isinstance(atom, list):
				return self.execlist(atom)
			elif isinstance(atom, str):
				if atom not in self.variables:
					self.variables[atom] = None
				return self.variables[atom]
			else:
				return atom
		except:
			print atom
			raise

	def execlist(self, atom):
		func, rest = atom[0], atom[1:]
		if func == '=':
			name, val = rest
			self.variables[name] = self.execute(val)
		else:
			rest = map(self.execute, rest)
			if func not in gfuncs:
				print 'func not found', func
				sys.exit(1)
			return gfuncs[func](*rest)

def run(code, **external_defaults):
	return Runner(code, **external_defaults).variables

if __name__=='__main__':
	print run(file('test.cdef', 'r').read(), init=0, chunk=[0, 1, 2, 3, ord('f'), ord('o'), ord('o'), ord('b')])
