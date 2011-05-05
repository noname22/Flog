import struct

class NetworkError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)	

class Protocol:
	def __init__(self, s):
		closed = False
		self.s = s

	def read_exactly(self, numbytes):
		data = ""
		for i in range(numbytes):
			data += self.s.recv(1)

		if len(data) < numbytes:
			raise NetworkError('connection closed')

		return data

	def write_exactly(self, data):
		for i in range(len(data)):
			self.s.send(data[i])

	def write_string(self, string):
		self.write_exactly(struct.pack("!I", len(string)))
		self.write_exactly(string)

	def read_uint32(self):
		r = self.read_exactly(4)
		return struct.unpack("!I", r)[0]
	
	def read_uint8(self):
		r = self.read_exactly(1)
		return struct.unpack("!B", r)[0]
	
	def read_uint64(self):
		r = self.read_exactly(8)
		return struct.unpack("!Q", r)[0]

	def read_string(self):
		len = self.read_uint32()
		return self.read_exactly(len)
