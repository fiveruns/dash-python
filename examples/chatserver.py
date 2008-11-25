# Requires the 

import gc, os, sys,signal

from twisted.internet import reactor
from twisted.protocols import basic

sys.path.append('..')

class MyChat(basic.LineReceiver):
  
    def connectionMade(self):
        print "Got new client!"
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        print "Lost a client!"
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        print "received", repr(line)
        for c in self.factory.clients:
            c.message(line)

    def message(self, message):
        self.transport.write('> ' + message + '\n')


from twisted.internet import protocol
from twisted.application import service, internet

factory = protocol.ServerFactory()
factory.protocol = MyChat
factory.clients = []

# ======================
# = DASH CONFIGURATION =
# ======================

# Hit local server
os.environ['DASH_UPDATE'] = 'http://localhost:3000'

import fiveruns_dash

# Custom metrics for this app
config = fiveruns_dash.configure(app_token = 'e7337bfd0b26a5708bbb4d8f552d25334c3473c8')
config.counter("messages", "Messages Processed", wrap = MyChat.message)
config.absolute("connections", "Number of Connections", call = (len, factory.clients))

# Beginnings of the 'python' recipe; for now we just add a metric or two
# directly to the config vs creating a real recipe object (TODO)

def refcount():
  ''' Get number of system refcounts total. '''
  return len(gc.get_objects())
  
config.absolute("gc_objects", "Number of GC tracked objects",
  call = refcount, recipe_name = 'python', recipe_url = 'http://dash.fiveruns.com')

# Start reporter
session = fiveruns_dash.start(config)

# Tell Twisted to shut-down the reporter politely (Python threading very polite)
reactor.addSystemEventTrigger('before', 'shutdown', session.stop)

# ===============
# = APP STARTUP =
# ===============

application = service.Application("chatserver")
internet.TCPServer(9090, factory).setServiceParent(application)