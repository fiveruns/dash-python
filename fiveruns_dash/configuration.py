import os, sys, logging

import metrics
import recipes

logger = logging.getLogger('fiveruns_dash.metrics')

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

  def add_recipe(self, name, url = None):
    """
    Add metrics from a recipe to this configuration.
 
    name -- A Recipe instance or String
    url -- A String, required to lookup the recipe if the name argument is not a Recipe instance
    """
    if isinstance(name, recipes.Recipe):
      self._replay_recipe(name)
    else:
      self.add_recipe(recipes.find(name, url))

  def _replay_recipe(self, recipe):
    pass

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
      
