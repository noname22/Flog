import sqlite3, Queue

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

