import os, sys

import metrics
from logging import log

class MetricSetting(object):
  
  def __init__(self):
    self.metrics = {}
  
  def time(self, name, description, **options):
    "Add a time metric"
    self.metrics[name] = metrics.TimeMetric(name, description, **options)

  def counter(self, name, description, **options):
    "Add a counter metric"
    self.metrics[name] = metrics.CounterMetric(name, description, **options)

  def absolute(self, name, description, **options):
    "Add an absolute metric"
    self.metrics[name] = metrics.AbsoluteMetric(name, description, **options)

  def percentage(self, name, description, **options):
    "Add a percentage metric"
    self.metrics[name] = metrics.PercentageMetric(name, description, **options)
  

class Configuration(MetricSetting):

  def __init__(self, **options):
    super(Configuration, self).__init__()
    self.app_token = None
    # TODO: Extract these into a Session object
    self.vm_version = sys.version
    self.pid = os.getpid()
    self.pwd = os.getcwd()
    self.process_id = None
    self.report_interval = 60
    for k, v in options.iteritems():
      self.__dict__[k] = v

  def instrument(self):
    for metric in self.metrics.values():
      metric._instrument()
      
class Recipe(MetricSetting):
  """docstring for Recipe"""
  
  def __init__(self, name, url):
    super(Recipe, self).__init__()
    self.name = name
    self.url = url
    