import logging
import os
import sys

from configuration import Configuration
from recipes import Recipe
from session import Reporter

def start(config):
    config.instrument()
    reporter = Reporter(config)
    config.reporter = reporter
    reporter.start()
    return reporter
    
def configure(*args, **kwargs):
    """
    Returns a configuration with the arguments specified
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
    return Recipe(name, url)
    
class NullLoggingHandler(logging.Handler):
    def emit(self, record):
        pass

def _configure_logger():
    logger = logging.getLogger("fiveruns.dash")
    stream = logging.StreamHandler()
    logger.addHandler(stream)
    formatter = logging.Formatter("%(name)s [%(levelname)s] %(message)s")
    stream.setFormatter(formatter)
    logger.setLevel(logging.WARN)
    return logger

logger = _configure_logger()
