import gc
import logging
import os
import random
import sys
import time
import fiveruns.dash

logging.basicConfig(level=logging.DEBUG)

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
    
    @recipe.time("sleeps", "Time Spent Resting")
    def sleep(self):
        time.sleep(random.random() * 5)
    
    @recipe.counter("tallies", "Number of Tallies")
    def incr(self):
        self.tally += 1

    @config.add_exceptions_from()
    def raise_error(self):
        raise Exception("New Exception")


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
