import sys, os, gc

sys.path.insert(0, '..')

import fiveruns_dash

import fiveruns_dash
import time, random

class Foo(object):
  
  def __init__(self, name):
    self.name = name
    self.tally = 0
    
  def run(self):
    while True:
      self.sleep()
      self.incr()
      
  def sleep(self):
    time.sleep(random.random() * 5)
      
  def incr(self):
      self.tally += 1

if len(sys.argv) < 2:
  print sys.argv
  sys.exit("No app token given")

config = fiveruns_dash.configure(app_token = sys.argv[1])
config.counter("tallies", "Number of Tallies", wrap = Foo.incr, recipe_name = 'app', recipe_url = 'http://dash.fiveruns.com')
config.time("sleeps", "Time Spent Resting", wrap = Foo.sleep, recipe_name = 'app', recipe_url = 'http://dash.fiveruns.com')

# Beginnings of the 'python' recipe; for now we just add a metric or two
# directly to the config vs creating a real recipe object (TODO)

def refcount():
  ''' Get number of system refcounts total. '''
  return len(gc.get_objects())
  
config.absolute("gc_objects", "Number of GC tracked objects",
  call = refcount, recipe_name = 'python', recipe_url = 'http://dash.fiveruns.com')

dash = fiveruns_dash.start(config)

try:
  Foo("bar").run()
except KeyboardInterrupt:
  dash.stop()
  raise
