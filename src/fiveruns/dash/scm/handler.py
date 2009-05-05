import os, logging

logger = logging.getLogger('fiveruns.dash.scm')

class Handler(object):

    def __init__(self, match):
        self.data = {}
        self.match = match
        self.collected = self.collect()

    def collect(self):
        """
        Collect the data for this SCM

        Needs to be defined in each handler or an exception is raised.
        """
        raise NotImplementedError("Abstract")

    def missing(self, pkg):
        logger.warn("Missing `%s' package.  Unable to report SCM details" % pkg)

    def __getitem__(self, key):
        return self.data[key]

    def keys(self):
        return self.data.keys()

def handlers():
    """
    Returns a list of all the SCM handlers that are available.
    """
    return [f[:-3] for f in os.listdir(os.path.join(os.path.dirname(__file__), 'handlers'))
            if not f.startswith('__') and f.endswith('.py')]

def at(directory):
    for name in handlers():
        match = _grab(name, 'matches')(directory)
        if match:
            logger.info("Found SCM: %s" % name[1:])
            handler = _grab(name, 'Handler')(match)
            if handler.collected:
                return handler
    logger.warn("Could not find SCM")

def _grab(name, attrib):
    return getattr(__import__('fiveruns.dash.scm.handlers.%s' % name, {}, {}, [attrib]), attrib)

def ascend(matcher, dirname, name):
    """
    Walk up a directory structure looking for a matching location
    """
    if matcher(dirname, name):
        return dirname
    else:
        if dirname in ('/', ''):
            return False
        else:
            return ascend(matcher, *os.path.split(dirname))

