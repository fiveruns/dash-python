import sys, os

from configuration import Configuration
from session import Reporter

def start(config):
  config.instrument()
  reporter = Reporter(config)
  reporter.start()
  return reporter
  
def configure(*args, **kwargs):
  return Configuration(*args, **kwargs)