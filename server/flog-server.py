#!/usr/bin/python

import sqlite3, socket, thread, threading, struct, uuid, time, Queue, json
import BaseHTTPServer, wsgiref.simple_server

webSendQueue = Queue.Queue()

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

				print app
				print time_sent
				print time_received
				print file
				print line
				print severity
				print message
		
				db.insert_message(app, start_time, instance, time_sent, time_received, file, line, message, severity)
				webSendQueue.put({'app': app, 'start_time': start_time, 'instance': instance, 'time_sent': time_sent,\
				'time_received': time_received, 'file': file, 'severity': severity, 'message': message});
				
			except NetworkError, e:
				print e
				return

	print "unknown client type: %s" % type

ajax_html = """
<html>

<head>
<title>AJAX + wsgiref Demo</title>
<script language="Javascript">
function ajax_send() 
{
    hr = new XMLHttpRequest();

    hr.open("POST", "/", true);
    hr.setRequestHeader("Content-Type", 
        "application/x-www-form-urlencoded");

    hr.onreadystatechange = function() 
    {
        if (hr.readyState == 4){
        	document.getElementById("result").innerHTML = hr.responseText;
		addRow(hr.responseText);
	}
    }

    hr.send(document.f.word.value);
}

function update()
{
	hr = new XMLHttpRequest();
	hr.open("GET","messages", true);
	hr.onreadystatechange = function() 
	{
		if(hr.responseText != ""){
			//document.write(hr.responseText);
			var response = eval(hr.responseText);
			for(var i in response){
				addRow(response[i].message);
			}
		}
	}
	hr.send(null);

	timerID = self.setTimeout("update()", 100)
}

function addRow(data){
	var tbody = document.getElementById("msgbody");
	var row = document.createElement("tr");
	var td1 = document.createElement("td");
	td1.appendChild(document.createTextNode(data));
	var td2 = document.createElement("td");
	td2.appendChild (document.createTextNode("column 2"));
	row.appendChild(td1);
	row.appendChild(td2);
	tbody.appendChild(row);
}

</script>
</head>

<body onLoad="update()">
<center>
<form name="f" onsubmit="ajax_send(); return false;">
    <p> 
        <input name="word" type="text">
        <input value="Do It" type="submit">
    </p>
    <div id="result"></div>
</form>

<table>
  <tbody id="msgbody">
    <tr>
      <td>row1_column1</td><td>row1_column1</td>
    </tr>
  </tbody>
</table>

</center>
</body>
</html>
"""

def web_server(environ, start_response):
	print  environ["PATH_INFO"]
	if environ["PATH_INFO"] == "/messages":
		start_response("200 OK", [("content-type", "text/html")])

		send = []

		while not webSendQueue.empty():
			send.append(webSendQueue.get())
		
		return [json.dumps(send)]
		#clen = int(environ["CONTENT_LENGTH"])
		#return [environ["wsgi.input"].read(clen)]
	else:
		start_response("200 OK", [("content-type", "text/html")])
		return [ajax_html]

def web_thread():
	httpd = wsgiref.simple_server.make_server("", 8080, web_server)
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
