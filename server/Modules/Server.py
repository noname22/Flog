from Modules.Connection import *

import socket
import thread
import threading

class Server:
	cb_list = []

	def _new_connection(self, clientsock, addr):
		connection = Connection(clientsock, self.cb_list)
		connection.handle_connection()

	def add_message_callback(self, fun):
		self.cb_list.append(fun)

	def serve_forever(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serversock.bind(('localhost', 13000))
		serversock.listen(5)

		try:
			while 1:
				print 'waiting for connections...'
				clientsock, addr = serversock.accept()
				print '...connected from:', addr
				thread.start_new_thread(self._new_connection, (clientsock, addr))
		except KeyboardInterrupt:
			pass
