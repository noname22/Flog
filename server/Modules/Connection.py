from Modules.Message import *
from Modules.Db import *
from Modules.WebServer import *

import struct
import time
import uuid
import socket

class NetworkError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)	

class Connection:
	def __init__(self, s, cb_list):
		self.s = s
		self.cb_list = cb_list

	def _read_exactly(self, numbytes):
		data = ""
		for i in range(numbytes):
			data += self.s.recv(1)

		if len(data) < numbytes:
			raise NetworkError('connection closed')

		return data

	def _write_exactly(self, data):
		for i in range(len(data)):
			self.s.send(data[i])

	def _write_string(self, string):
		self._write_exactly(struct.pack("!I", len(string)))
		self._write_exactly(string)

	def _read_uint32(self):
		r = self._read_exactly(4)
		return struct.unpack("!I", r)[0]
	
	def _read_uint8(self):
		r = self._read_exactly(1)
		return struct.unpack("!B", r)[0]
	
	def _read_uint64(self):
		r = self._read_exactly(8)
		return struct.unpack("!Q", r)[0]

	def _read_string(self):
		len = self._read_uint32()
		return self._read_exactly(len)

	def _read_message(self, instance, start_time):
		app = self._read_string()
		time_sent = float(self._read_uint64()) / 1000.0
		time_received = time.time()
		file = self._read_string()
		line = self._read_uint32()
		severity = self._read_uint8()
		message = self._read_string()

		return Message(app, time_sent, time_received, file, line, severity, message, start_time, instance);

	def _logger_connection(self):
		instance = str(uuid.uuid4())
		start_time = time.time()

		while 1:
			try:
				m = self._read_message(instance, start_time);
				for cb in self.cb_list:
					cb(m)

			except NetworkError, e:
				print e
				return


	def handle_connection(self):
		handshake = self._read_string()
		
		if handshake != "flog":
			print "invalid handshake from client"

		type = self._read_string()
		protocol_version = self._read_uint32()

		print "client is a %s and speaks protocol version %d" % (type, protocol_version)

		self._write_string("ok")

		if type == "logger":
			self._logger_connection()
		else:
			print "unknown client type: %s" % type
