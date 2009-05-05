import logging
import os
import sys
import traceback

import aspects

import metrics
import recipes

logger = logging.getLogger('fiveruns.dash.metrics')

class Configuration(metrics.MetricSetting):

    def __init__(self, **options):
        super(Configuration, self).__init__()
        self.app_token = None
        # TODO: Extract these into a Session object
        self.vm_version = sys.version
        self.pid = os.getpid()
        self.pwd = os.getcwd()
        self.extra_payload_data = {}
        self.process_id = None
        self.report_interval = 60
        self.reporter = None
        self.__dict__.update(**options)

    def add_exceptions_from(self, target):
        logger.debug("Capturing exceptions from %s" % target)
        aspects.with_wrap(self._capture_exceptions, target) 

    def instrument(self):
        for metric in self.metrics.values():
            metric._instrument()

    def _capture_exceptions(self, obj):
        try:
            yield aspects.proceed
        except Exception, e:
            if self.reporter:
                try:
                    self.reporter.add_exception(e)                
                except:
                    logger.debug("Could not add exception due to internal error: %s\n%s" % (sys.exc_info()[1], "\n".join(traceback.format_tb(sys.exc_info()[2]))))
            raise

    def _replay_recipe(self, recipe):
        logger.debug("Adding %d metric(s) from recipe `%s' for %s to configuration" % (
            len(recipe.metrics),
            recipe.name, recipe.url))
        super(Configuration, self)._replay_recipe(recipe)
