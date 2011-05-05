from Modules.Connection import *

import socket
import thread
import threading

class Server:
	cb_list = []

	def __init__(self, addr, port):
		self.port = port
		self.addr = addr

	def _new_connection(self, clientsock, addr):
		connection = Connection(clientsock, self.cb_list)
		connection.handle_connection()

	def add_message_callback(self, fun):
		self.cb_list.append(fun)

	def serve_forever(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serversock.bind((self.addr, self.port))
		serversock.listen(5)

		try:
			print "Listening for connections on %s, port %d" % (self.addr, self.port)
			while 1:
				clientsock, addr = serversock.accept()
				#print '...connected from:', addr
				thread.start_new_thread(self._new_connection, (clientsock, addr))
		except KeyboardInterrupt:
			pass
