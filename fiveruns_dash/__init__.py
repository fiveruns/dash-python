import sys, os, logging

class NullLoggingHandler(logging.Handler):
  def emit(self, record):
    pass

logging_handler = NullLoggingHandler()
logger = logging.getLogger("fiveruns_dash").addHandler(logging_handler)

from configuration import Configuration
from session import Reporter
from recipes import Recipe

def start(config):
  config.instrument()
  reporter = Reporter(config)
  config.reporter = reporter
  reporter.start()
  return reporter
  
def configure(*args, **kwargs):
  return Configuration(*args, **kwargs)

def recipe(name, url):
  return Recipe(name, url)
  
version_info = (0,2,0)
