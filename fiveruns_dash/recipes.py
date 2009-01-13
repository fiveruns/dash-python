import metrics, logging

logger = logging.getLogger('fiveruns_dash.recipes')

registry = {}

class Recipe:

  def __init__(self, name, url):
    self.name = name
    self.url = url
    self.metrics = {}
    self._register()
  
  def time(self, name, *args, **options):
    "Add a time metric"
    self._add_metric(metrics.TimeMetric, name, *args, **options)

  def counter(self, name, *args, **options):
    "Add a counter metric"
    self._add_metric(metrics.CounterMetric, name, *args, **options)

  def absolute(self, name, *args, **options):
    "Add an absolute metric"
    self_.add_metric(metrics.AbsoluteMetric, name, *args, **options)

  def percentage(self, name, *args, **options):
    "Add a percentage metric"
    self._add_metric(metrics.PercentageMetric, name, *args, **options)

  def _add_metric(self, metric_class, name, *args, **options):
    "Add a metric to this recipe"
    options['recipe_name'] = self.name
    options['recipe_url'] = self.url
    self.metrics[name] = metric_class(name, *args, **options)

  def _register(self):
    "Register this recipe"
    registry[(self.name, self.url)] = self
    logger.debug("Registered recipe `%s' for %s" % (self.name, self.url))

def find(name, url):
  "Find a registered recipe"
  if registry.has_key((name, url)):
    return registery[(name, url)]
  else:
    raise UnknownRecipe

class UnknownRecipe(NameError):
  """
  Raised when fiveruns_dash.recipes.find cannot find a requested recipe
  """

  def __init__(self, name, url):
    self.name = name
    self.url = url

  def __str__(self):
    return repr("%s (%s)" % (self.name, self.url))

  
