import sys, os, logging

class NullLoggingHandler(logging.Handler):
  def emit(self, record):
    pass

def _configure_logger():
  logger = logging.getLogger("fiveruns_dash")
  stream = logging.StreamHandler()
  logger.addHandler(stream)
  formatter = logging.Formatter("%(name)s [%(levelname)s] %(message)s")
  stream.setFormatter(formatter)
  logger.setLevel(logging.WARN)
  return logger

logger = _configure_logger()

def start(config):
  from session import Reporter
  config.instrument()
  reporter = Reporter(config)
  config.reporter = reporter
  reporter.start()
  return reporter
  
def configure(*args, **kwargs):
  from configuration import Configuration
  """
  Returns a configuration with the arguments specified
  from configuration import Configuration
  """
  return Configuration(*args, **kwargs)

def recipe(name, url):
  """
  Register and return a new recipe for name and url.

  >>> recipe1 = recipe('foo', 'http://example.com')
  >>> recipe1 # doctest: +ELLIPSIS
  <recipes.Recipe object at 0x...>
  >>> recipes.registry[('foo', 'http://example.com')] == recipe1
  True

  If a recipe is already defined by the name and url, a
  RegistrationError is raised

  >>> recipes.registry[('foo', 'http://example.com')] == recipe1
  True
  >>> recipe('foo', 'http://example.com')
  Traceback (most recent call last):
    ...
  DuplicateRecipe: `foo' defined for `http://example.com'
  """
  from recipes import Recipe
  return Recipe(name, url)
  
version_info = (0,2,1)

if __name__ == "__main__":
    import recipes
    import doctest
    doctest.testmod()
