#!/usr/bin/python

from Modules.Server import *
from Modules.Db import *
from Modules.WebServer import *
from Modules.StdOut import *

import thread
import threading

def Main():
	server = Server()
	db = Db()
	web_server = WebServer()
	stdout = StdOut()

	thread.start_new_thread(web_server.serve_forever, ())
	thread.start_new_thread(db.serve_forever, ())

	server.add_message_callback(db.insert_message)
	server.add_message_callback(web_server.send_message)
	server.add_message_callback(stdout.print_message)

	server.serve_forever()

if __name__ == '__main__': Main()
