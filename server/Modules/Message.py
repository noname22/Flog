import datetime

class Message:
	def __init__(self, app = '', time_sent = 0, time_received = 0, file = '', line = 0, severity = 0, message = '', start_time = 0, instance = ''):
		self.app = app
		self.time_sent = time_sent
		self.time_received = time_received
		self.file = file
		self.line = line
		self.severity = severity
		self.message = message
		self.start_time = start_time
		self.instance = instance

	def severity_as_string(self):
		try:
			return {1: 'D1', 2:'D2', 4:'D3', 8:'VV', 16:'II', 32:'WW', 64:'EE', 128:'FF'}[self.severity]
		except KeyError:
			return "??"

	def to_string(self):
		d = datetime.datetime.fromtimestamp(self.time_sent).strftime("%X")
		file = self.file

		if len(file) > 16:
			file = "...%s" % file[-15:]

		return "%s %s %s [%s] %s:%d %s" % (self.app, self.instance[-8:], d, self.severity_as_string(),\
			 file, self.line, self.message)

	def to_struct(self):
		return {'app': self.app, 'start_time': self.start_time, 'instance': self.instance,\
			'time_sent': self.time_sent, 'time_received': self.time_received, 'file': self.file,\
			 'line': self.line, 'severity': self.severity, 'message': self.message};
