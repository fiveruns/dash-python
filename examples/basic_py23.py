'''
This example works with Python 2.3
'''
import gc
import logging
import os
import random
import sys
import time
import fiveruns.dash

logging.basicConfig()

if len(sys.argv) < 2:
    sys.exit("No app token given")

config = fiveruns.dash.configure(app_token=sys.argv[1])
recipe = fiveruns.dash.recipe('app', 'http://dash.fiveruns.com')


class Foo(object):
    
    def __init__(self, name):
        self.name = name
        self.tally = 0
        
    def run(self):
        while True:
            try:
                self.raise_error()
            except:
                pass
            self.sleep()
            self.incr()
    
    def sleep(self):
        time.sleep(random.random() * 5)
    sleep = recipe.time("sleeps", "Time Spent Resting")(sleep)
    
    def incr(self):
        self.tally += 1
    incr = recipe.counter("tallies", "Number of Tallies")(incr)

    def raise_error(self):
        raise Exception("New Exception")
    raise_error = config.add_exceptions_from()(raise_error)


config.add_recipe('app')

#add default python recipe to our configuration
fiveruns.dash.register_default_recipe()
config.add_recipe('python', 'http://dash.fiveruns.com')

dash = fiveruns.dash.start(config)

try:
    Foo("bar").run()
except KeyboardInterrupt:
    dash.stop()
    raise
