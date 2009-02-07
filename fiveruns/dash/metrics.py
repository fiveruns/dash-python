from __future__ import with_statement
from threading import RLock
import time
import logging
import copy

import aspects

logger = logging.getLogger('fiveruns.dash.metrics')

class MetricError(StandardError):
    pass

class Calculation(object):
    def __init__(self, operation, *fields):
        self.operation = operation
        self.fields = fields

    def run(self, *args):
        return self.operation(*args)

class Metric(object):

    def __init__(self, name, description, **options):
        self.info_id = None
        self.name = name
        self.description = description
        self.options = options
        self.containers = {}
        self.context_finder = None
        self.unit = None
        self.data_type = self._data_type()
        self.recipe_name = options.get('recipe_name', None)
        self.recipe_url = options.get('recipe_url', None)
        self.help_text = None
        self.calculation = options.get('calculation', None)
        self.lock = RLock()
        self._validate()
        logger.debug("Defined %s metric `%s' (recipe `%s' for `%s')" % (self.data_type, self.name, self.recipe_name, self.recipe_url))

    def virtual(self):
        if self.calculation:
            return True
        else:
            return False
    virtual = property(virtual)

    def calculate(self, data):
        """
        Used if this metric is virtual

        Note: Does not support time metrics
        """
        logger.debug("Preparing to calculate metric %s from data:\n%s" % (self.name, data))
        if not self.virtual:
            return []
        else:
            results = []
            sets = {}
            for field in self.calculation.fields:
                logger.debug("Getting data for field `%s'" % field)
                for record in data.get((field, self.recipe_name, self.recipe_url), {'values':[]})['values']:
                    logger.debug("Data is `%s'" % record)
                    if record['content'] not in sets:
                        sets[record['context']] = {}
                    sets[record['context']][field] = record['value']
            logger.debug("Sets is %s" % sets)
            for context, field_data in sets.iteritems():
                if len(field_data) == len(self.calculation.fields):
                    logger.debug("Enough data to calculate %s; doing it..." % self.name)
                    args = [field_data[field] for field in self.calculation.fields]
                    value = self.calculation.run(*args)
                    results.append({'context':context, 'value':value})
                else:
                    logger.debug("Not enough data to calculate %s" % self.name)
            return results

    def values(self):
        """
        Used if this metric isn't virtual
        """
        logger.debug("Snapshotting metric %s" % self.name)
        return self._snapshot()

    def _container_for_context(self, context):
        if context in self.containers:
            return self.containers[context]
        else:
            container =  self._default_container_for(context)
            self.containers[context] = container
            return container

    def _default_container_for(self, context):
        return {"context" : context, "value" : 0}

    def _current_context(self, obj, *args, **kwargs):
        if self.context_finder:
            return self.context_finder(obj, *args, **kwargs)
        else:
            return None  

    def metadata(self):
        result = {}
        for field in ['name', 'unit', 'description', 'help_text', 'recipe_name', 'recipe_url']:
            result[field] = self.__dict__[field]
        result['data_type'] = self._data_type()
        return result

    def _instrument(self):
        pass
          
    def _record(self, func):
        """
        Call custom function and merge its result into containers
        """
        receiver = func
        args = []
        if isinstance(receiver, tuple):
            receiver = func[0]
            args = func[1:]
            result = receiver(*args)
            with self.lock:
                if isinstance(result, dict):
                    self.containers.update(result)
                else:
                    # TODO: Support context_finder & pre-defined contexts
                    container = self._container_for_context(None)
                    container["value"] = result
      
    def _snapshot(self):
        """
        Retrieve existing data for this metric, and reset it
        # TODO Make threadsafe
        """
        with self.lock:
            values = self.containers.values()
            self.containers = {}
            return values
    
class CounterMetric(Metric):

    def values(self):
        if self.virtual:
            return True
        if 'call' in self.options:
            self._record(self.options['call'])
        return self._snapshot()

    def _validate(self):
        if 'wrap' not in self.options and 'call' not in self.options:
            raise MetricError("Required `wrap' or `sources' option")

    def _instrument(self):
        self._wrap(self.options.get('wrap', []))

    def _wrap(self, target):
        if callable(target):
            logger.debug("%s wrapping %s" % (self, target))
            aspects.with_wrap(self._wrapper, target)
        else:
            for item in target:
                self._wrap(item)

    def _wrapper(self, obj, *args, **kwargs):
        with self.lock:
            context = self._current_context(obj, *args, **kwargs)
            container = self._container_for_context(context)
            container["value"] += 1
            yield aspects.proceed

    def _data_type(self):
        return 'counter'
  
        
class TimeMetric(Metric):

    def _default_container_for(self, context):
        return {"context" : context, "invocations" : 0, "value" : 0}

    def _validate(self):
        if self.virtual:
            return True
        if 'wrap' not in self.options:
            raise MetricError("Required `wrap'")

    def _instrument(self):
        self._wrap(self.options.get('wrap', []))

    def _wrap(self, target):
        if callable(target):
            logger.debug("%s wrapping %s" % (self, target))
            aspects.with_wrap(self._wrapper, target)
        else:
            for item in target:
                self._wrap(item)

    def _wrapper(self, obj, *args, **kwargs):
        with self.lock:
            context = self._current_context(obj, *args, **kwargs)
            container = self._container_for_context(context)
            start = time.time()
            yield aspects.proceed
            value = time.time() - start
            container["value"] += value
            container["invocations"] += 1

    def _data_type(self):
        return 'time'

class AbsoluteMetric(Metric):

    def _validate(self):
        if self.virtual:
            return True
        if 'call' not in self.options:
            raise MetricError("Required `call'")

    def values(self):
        self._record(self.options['call'])
        return self._snapshot()

    def _data_type(self):
        return 'absolute'

class PercentageMetric(Metric):

    def _validate(self):
        if self.virtual:
            return True
        if 'call' not in self.options:
            raise MetricError("Required `call'")

    def values(self):
        self._record(self.options['call'])
        return self._snapshot()

    def _data_type(self):
        return 'percentage'

class MetricSetting(object):

    def __init__(self):
        self.metrics = {}

    def time(self, name, *args, **options):
        "Add a time metric"
        self._add_metric(TimeMetric, name, *args, **options)

    def counter(self, name, *args, **options):
        "Add a counter metric"
        self._add_metric(CounterMetric, name, *args, **options)

    def absolute(self, name, *args, **options):
        "Add an absolute metric"
        self._add_metric(AbsoluteMetric, name, *args, **options)

    def percentage(self, name, *args, **options):
        "Add a percentage metric"
        self._add_metric(PercentageMetric, name, *args, **options)

    def add_recipe(self, name, url = None):
        """
        Add metrics from a recipe to this configuration.

        name -- A Recipe instance or String
        url -- A String, required to lookup the recipe if the name argument is not a Recipe instance
        """
        if isinstance(name, str):
            self.add_recipe(recipes.find(name, url))
        else:
            self._replay_recipe(name)

    def _replay_recipe(self, recipe):
        self.metrics.update(recipe.metrics)

    def _add_metric(self, metric_class, name, *args, **options):
        "Add a metric"
        metric =  metric_class(name, *args, **options)
        self.metrics[(metric.name, metric.recipe_name, metric.recipe_url)] = metric

import recipes
