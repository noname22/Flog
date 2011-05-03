#!/usr/bin/python

import sqlite3, socket, thread, threading, struct, uuid, time, Queue

class Db:
	def __init__(self):
		self.cmdQueue = Queue.Queue()

		self.conn = sqlite3.connect('flog.sqlite')
		self.cursor = self.conn.cursor()

		self.cursor.execute("""create table if not exists messages 
			(
				application TEXT, 
				start_time FLOAT, 
				instance INTEGER, 
				time_sent INTEGER, 
				time_recieved FLOAT, 
				file_name TEXT, 
				line_number INTEGER, 
				message TEXT, 
				severity INTEGER
			)""")
	def processQueue(self):
		while not self.cmdQueue.empty():
			self.cursor.execute(self.cmdQueue.get())

		self.conn.commit()

	def insert_message(self, application, start_time, instance, time_sent, time_received, file_name, line_number, message, severity):
		self.cmdQueue.put("""insert into messages values
			(
				'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'
			)""" % (application, start_time, instance, time_sent, time_received, file_name, line_number, message, severity))

	def list_messages(self):
		self.cursor.execute("select * from messages")
		return self.cursor.fetchall()

class NetworkError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)	

class SocketReader:
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

def db_thread():
	global db
	db = Db()
	while 1:
		db.processQueue()
		time.sleep(0.1)

def handle_connection(clientsock, addr):
	reader = SocketReader(clientsock)

	instance = uuid.uuid4()
	start_time = time.time()

	handshake = reader.read_string()
	
	if handshake != "flog":
		print "invalid handshake from client"

	type = reader.read_string()
	protocol_version = reader.read_uint32()

	print "client is a %s and speaks protocol version %d" % (type, protocol_version)

	reader.write_string("ok")

	if type == "logger":
		while 1:
			try:
				app = reader.read_string()
				time_sent = float(reader.read_uint64()) / 1000.0
				time_received = time.time()
				file = reader.read_string()
				line = reader.read_uint32()
				severity = reader.read_uint8()
				message = reader.read_string()

				print app
				print time_sent
				print time_received
				print file
				print line
				print severity
				print message
		
				db.insert_message(app, start_time, instance, time_sent, time_received, file, line, message, severity)
				
			except NetworkError, e:
				print e
				return

	print "unknown client type: %s" % type


thread.start_new_thread(db_thread, ())

serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversock.bind(('localhost', 13000))
serversock.listen(5)

while 1:
	print 'waiting for connections...'
	clientsock, addr = serversock.accept()
	print '...connected from:', addr
	thread.start_new_thread(handle_connection, (clientsock, addr))


#db.insert_message("test", 123, 123, 123, 123, "test.cpp", 100, "test", 1)
#print db.list_messages()
