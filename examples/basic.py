import sys, os, gc, logging

sys.path.insert(0, '..')

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

logger = logging.getLogger('fiveruns_dash')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

recipe = fiveruns_dash.recipe('app', 'http://dash.fiveruns.com')
recipe.counter("tallies", "Number of Tallies", wrap = Foo.incr)
recipe.time("sleeps", "Time Spent Resting", wrap = Foo.sleep)

config = fiveruns_dash.configure(app_token = sys.argv[1])
config.add_recipe(recipe)

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
