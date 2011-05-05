#!/usr/bin/python

from Modules.Db import *
from Modules.Protocol import *
from Modules.WebServer import *

import socket, thread, threading, struct, uuid, time, Queue

def db_thread():
	global db
	db = Db()
	while 1:
		db.processQueue()
		time.sleep(0.1)

def handle_connection(clientsock, addr):
	reader = Protocol(clientsock)

	instance = str(uuid.uuid4())
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

				#print app
				#print time_sent
				#print time_received
				#print file
				#print line
				#print severity
				#print message
		
				db.insert_message(app, start_time, instance, time_sent, time_received, file, line, message, severity)
				webSendQueue.put({'app': app, 'start_time': start_time, 'instance': instance, 'time_sent': time_sent,\
				'time_received': time_received, 'file': file, 'line': line, 'severity': severity, 'message': message});
				
			except NetworkError, e:
				print e
				return

	print "unknown client type: %s" % type

def web_thread():
	httpd = wsgiref.simple_server.make_server("", 8080, web_server, handler_class=RequestHandler)
	httpd.serve_forever()

thread.start_new_thread(web_thread, ())
thread.start_new_thread(db_thread, ())

serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversock.bind(('localhost', 13000))
serversock.listen(5)

try:
	while 1:
		print 'waiting for connections...'
		clientsock, addr = serversock.accept()
		print '...connected from:', addr
		thread.start_new_thread(handle_connection, (clientsock, addr))
except KeyboardInterrupt:
	pass

#db.insert_message("test", 123, 123, 123, 123, "test.cpp", 100, "test", 1)
#print db.list_messages()
