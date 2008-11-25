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
      
  
config = fiveruns_dash.Configuration()
config.app_token = '67a47d5f6ce27fbe233af824b2d5b8ce10b5a54c'
config.counter("tallies", "Number of Tallies", wrap = Foo.incr, recipe_name = 'python', recipe_url = 'http://dash.fiveruns.com')
config.time("sleeps", "Time Spent Resting", wrap = Foo.sleep, recipe_name = 'python', recipe_url = 'http://dash.fiveruns.com')

dash = fiveruns_dash.start(config)

try:
  Foo("bar").run()
except KeyboardInterrupt:
  dash.stop()
  raise