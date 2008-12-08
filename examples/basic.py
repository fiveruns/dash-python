import sys, os, gc

sys.path.append('..')

os.environ['DASH_UPDATE'] = 'https://dash-collector-staging.fiveruns.com'

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
      
config = fiveruns_dash.configure(app_token = 'd756ed4bc66f1b28f1e3ed7b2d69a6a2c55c65a1')
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