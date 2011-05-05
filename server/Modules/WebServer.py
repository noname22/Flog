import BaseHTTPServer, wsgiref.simple_server, Queue, json
from wsgiref.handlers import SimpleHandler
from BaseHTTPServer import BaseHTTPRequestHandler
from wsgiref.simple_server import WSGIRequestHandler
from wsgiref.handlers import SimpleHandler

webSendQueue = Queue.Queue()

class RequestHandler(WSGIRequestHandler):
	def handle(self):
		self.raw_requestline = self.rfile.readline()
		if not self.parse_request(): # An error code has been sent, just exit
			return

		handler = SimpleHandler(
			self.rfile, self.wfile, self.get_stderr(), self.get_environ()
		)
		handler.request_handler = self	  # backpointer for logging
		handler.run(self.server.get_app())


def web_server(environ, start_response):
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
		f = open('Files/viewer.html')
		viewer = f.read()
		f.close()
		return [viewer]

