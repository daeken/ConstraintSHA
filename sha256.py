import struct
from runner import run

teststr = 'abc'

chunk = teststr + '\x80'
while len(chunk) != (448 / 8):
	chunk += '\0'
chunk += struct.pack('>Q', len(teststr) * 8)
chunk = list(struct.unpack('>' + 'L' * (512 / 32), chunk))

defs = dict(
	h0=0x6a09e667, 
	h1=0xbb67ae85, 
	h2=0x3c6ef372, 
	h3=0xa54ff53a, 
	h4=0x510e527f, 
	h5=0x9b05688c, 
	h6=0x1f83d9ab, 
	h7=0x5be0cd19, 
	chunk=chunk
)

vars = run(file('sha256.cdef', 'r').read(), **defs)
print ' '.join('%08x' % vars['final%i_0' % i] for i in xrange(8))

import hashlib
print 'official', hashlib.sha256(teststr).hexdigest()
