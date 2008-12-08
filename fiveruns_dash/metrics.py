from __future__ import with_statement
from threading import RLock
import aspects, time

from logging import log

class MetricError(StandardError): pass

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
    self.lock = RLock()
    self._validate()
    
  def values(self):
    return self._snapshot()
                
  def _container_for_context(self, context):
    if self.containers.has_key(context):
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
      
  def _instrument(self): pass
          
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
    if self.options.has_key('call'):
      self._record(self.options['call'])
    return self._snapshot()
  
  def _validate(self):
    if not (self.options.has_key('wrap') or self.options.has_key('call')):
      raise MetricError("Required `wrap' or `call' option")
      
  def _instrument(self):
    if self.options['wrap']:
      aspects.with_wrap(self._wrapper, self.options['wrap'])   
      
  def _wrapper(self, obj, *args, **kwargs):
    with self.lock:
      context = self._current_context(obj, *args, **kwargs)
      container = self._container_for_context(context)
      container["value"] += 1
    yield aspects.proceed
    
  def _data_type(self): return 'counter'
  
        
class TimeMetric(Metric):
  
  def _default_container_for(self, context):
    return {"context" : context, "invocations" : 0, "value" : 0}
  
  def _validate(self):
    if not (self.options.has_key('wrap')):
      raise MetricError("Required `wrap'")
  
  def _instrument(self):
    aspects.with_wrap(self._wrapper, self.options['wrap'])    
  
  def _wrapper(self, obj, *args, **kwargs):
    with self.lock:
      context = self._current_context(obj, *args, **kwargs)
      container = self._container_for_context(context)
      start = time.time()      
      yield aspects.proceed
      value = time.time() - start
      container["value"] += value
      container["invocations"] += 1
  
  def _data_type(self): return 'time'
    
class AbsoluteMetric(Metric):
  
  def _validate(self):
    if not (self.options.has_key('call')):
      raise MetricError("Required `call'")

  def values(self):
    self._record(self.options['call'])
    return self._snapshot()
  
  def _data_type(self): return 'absolute'
    
class PercentageMetric(Metric):
  
  def _validate(self):
    if not (self.options.has_key('call')):
      raise MetricError("Required `call'")

  def values(self):
    self._record(self.options['call'])
    return self._snapshot()
  
  def _data_type(self): return 'percentage'
