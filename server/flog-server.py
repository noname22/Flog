#!/usr/bin/python

import sqlite3, socket, thread, threading

class Db:
	def __init__(this):
		this.mutex = threading.mutex.mutex
		this.conn = sqlite3.connect('flog.sqlite')
		this.cursor = this.conn.cursor()

		this.cursor.execute("""create table if not exists messages 
			(
				application TEXT, 
				start_time INTEGER, 
				instance INTEGER, 
				time_sent INTEGER, 
				time_recieved INTEGER, 
				file_name TEXT, 
				line_number INTEGER, 
				message TEXT, 
				severity INTEGER
			)""")

	def insert_message(this, application, start_time, instance, time_sent, time_received, file_name, line_number, message, severity):
		this.mutex.lock()
		this.cursor.execute("""insert into messages values
			(
				'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'
			)""" % (application, start_time, instance, time_sent, time_received, file_name, line_number, message, severity))
		this.conn.commit()
		this.mutex.unlock()

	def list_messages(this):
		this.mutex.lock()
		this.cursor.execute("select * from messages")
		ret = this.cursor.fetchall()
		this.mutex.unlock()
		return ret



def handle_connection(clientsock, addr):
	while 1:
		data = clientsock.recv(1024)
		if not data: 
			break

		
		#clientsock.send('... %s' % data)

db = Db()

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
