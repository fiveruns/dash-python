import sys, os, logging

class NullLoggingHandler(logging.Handler):
  def emit(self, record):
    pass

logging_handler = NullLoggingHandler()
logger = logging.getLogger("fiveruns_dash").addHandler(logging_handler)

def start(config):
  from session import Reporter
  config.instrument()
  reporter = Reporter(config)
  config.reporter = reporter
  reporter.start()
  return reporter
  
def configure(*args, **kwargs):
  from configuration import Configuration
  return Configuration(*args, **kwargs)

def recipe(name, url):
  from recipes import Recipe
  return Recipe(name, url)
  
version_info = (0,2,1)
