import BaseHTTPServer
import wsgiref.simple_server
import Queue
import json

from wsgiref.handlers import SimpleHandler
from BaseHTTPServer import BaseHTTPRequestHandler
from wsgiref.simple_server import WSGIRequestHandler
from wsgiref.handlers import SimpleHandler

class _RequestHandler(WSGIRequestHandler):
	def handle(self):
		self.raw_requestline = self.rfile.readline()
		if not self.parse_request(): # An error code has been sent, just exit
			return

		handler = SimpleHandler(
			self.rfile, self.wfile, self.get_stderr(), self.get_environ()
		)
		handler.request_handler = self	  # backpointer for logging
		handler.run(self.server.get_app())

class WebServer:
	send_queue = Queue.Queue()
	cb_list = []

	def __init__(self):
		self.httpd = wsgiref.simple_server.make_server("", 8080, self._handle_request, handler_class=_RequestHandler)

	def add_new_viewer_callback(self, fun):
		cb_list.append(fun)
	
	def _handle_request(self, environ, start_response):
		if environ["PATH_INFO"] == "/messages":
			start_response("200 OK", [("content-type", "text/html")])

			send = []

			while not self.send_queue.empty():
				send.append(self.send_queue.get())
			
			return [json.dumps(send)]
			#clen = int(environ["CONTENT_LENGTH"])
			#return [environ["wsgi.input"].read(clen)]
		else:
			start_response("200 OK", [("content-type", "text/html")])

			f = open('Files/viewer.html')
			viewer = f.read()
			f.close()

			for cb in self.cb_list:
				cb(self)

			return [viewer]

	def serve_forever(self):
		self.httpd.serve_forever()

	def send_message(self, m):
		self.send_queue.put(m.to_struct())
