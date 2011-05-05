import sqlite3
import Queue
import time

class Db:
	def __init__(self):
		self.cmdQueue = Queue.Queue()

	def _connect(self):
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
		

	def _process_queue(self):
		while not self.cmdQueue.empty():
			self.cursor.execute(self.cmdQueue.get())

		self.conn.commit()

	def insert_message(self, m):
		self.cmdQueue.put("""insert into messages values
			(
				'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'
			)""" % (m.app, m.start_time, m.instance, m.time_sent, \
				m.time_received, m.file, m.line, m.message, m.severity))

	def list_messages(self):
		self.cursor.execute("select * from messages")
		return self.cursor.fetchall()
	
	def serve_forever(self):
		self._connect()
		while 1:
			self._process_queue()
			time.sleep(0.1)
