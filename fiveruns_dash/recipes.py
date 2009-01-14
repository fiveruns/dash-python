import metrics, logging

logger = logging.getLogger('fiveruns_dash.recipes')

registry = {}

class Recipe(metrics.MetricSetting):

  def __init__(self, name, url):
    super(Recipe, self).__init__()
    self.name = name
    self.url = url
    self._register()

  def _add_metric(self, *args, **options):
    "Add a metric"
    options['recipe_name'] = self.name
    options['recipe_url'] = self.url
    super(Recipe, self)._add_metric(*args, **options)

  def _register(self):
    "Register this recipe"
    registry[(self.name, self.url)] = self
    logger.debug("Registered recipe `%s' for `%s'" % (self.name, self.url))

  def _replay_recipe(self, recipe):
    logger.debug("Adding %d metric(s) from recipe `%s' for `%s' to recipe `%s' for `%s'" % (
      len(recipe.metrics),
      recipe.name, recipe.url,
      self.name, self.url))
    super(Recipe, self)._replay_recipe(recipe)

def find(name, url):
  "Find a registered recipe"
  if registry.has_key((name, url)):
    return registry[(name, url)]
  else:
    raise UnknownRecipe(name, url)

class UnknownRecipe(NameError):
  """
  Raised when fiveruns_dash.recipes.find cannot find a requested recipe
  """

  def __init__(self, name, url):
    self.name = name
    self.url = url

  def __str__(self):
    return "`%s' for `%s'" % (self.name, self.url)

  
