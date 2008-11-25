from __future__ import with_statement
import time, signal, sys, os, zlib
import aspects
from types import *
import httplib, mimetypes, simplejson, urlparse
from threading import Thread, RLock
from StringIO import StringIO

def start(config):
  config.instrument()
  reporter = Reporter(config)
  reporter.start()
  return reporter
  
def configure(*args, **kwargs):
  return Configuration(*args, **kwargs)
  
class Configuration(object):
  
  def __init__(self, **options):
    self.metrics = {}
    self.app_token = None
    # TODO: Extract these into a Session object
    self.vm_version = sys.version
    self.pid = os.getpid()
    self.pwd = os.getcwd()
    self.process_id = None
    self.report_interval = 60
    for k, v in options.iteritems():
      self.__dict__[k] = v
  
  def time(self, name, description, **options):
    "Add a time metric"
    self.metrics[name] = TimeMetric(name, description, **options)
    
  def counter(self, name, description, **options):
    "Add a counter metric"
    self.metrics[name] = CounterMetric(name, description, **options)
    
  def absolute(self, name, description, **options):
    "Add an absolute metric"
    self.metrics[name] = AbsoluteMetric(name, description, **options)
    
  def percentage(self, name, description, **options):
    "Add a percentage metric"
    self.metrics[name] = PercentageMetric(name, description, **options)
    
  def instrument(self):
    for metric in self.metrics.values():
      metric._instrument()
      
class Payload(object):
  
  DEFAULT_HOST = 'https://dash-collector.fiveruns.com'

  def __init__(self, config):
    self.config = config
    self.data = self._extract_data()
        
  def send(self):
    urlparts = urlparse.urlparse(os.environ['DASH_UPDATE'] or DEFAULT_HOST)
    (status, reason, body) = post_multipart(
      urlparts.netloc,
      self.path(),
      self._extra_params(),
      [('file', 'data.json.gz', self._compressed())]
    )
    if status == 201:
      self._succeeded(body)
      return True
    elif status in range(400, 499):
      self._failed(reason)
    else:
      self._unknown(status, reason)
    return False # TODO: HTTP
  
  def _succeeded(self, body):
    log("Succeeded.")
    
  def _failed(self, reason):
    log("Failed (%s)" % reason)
  
  def _unknown(self, status, reason):
    log("Unknown error (%s, %s)" % (status, reason))
    
  def _extra_params(self):
    return [
      ('app_id', self.config.app_token),
      ('ip', '127.0.0.1'), # FIXME
      ('pid', str(self.config.pid)),
      ('pwd', self.config.pwd),
      ('vm_version', self.config.vm_version),
      ('process_id', self.config.process_id and str(self.config.process_id) or '')
    ]
    
  def _compressed(self):
    return zlib.compress(self._serialize())
    
  def _serialize(self):
    return simplejson.dumps(self.data)
    
      
class InfoPayload(Payload):
  """
  Sample data structure:
  
    {
      "metric_infos": [
        {"name":"rss","data_type":"absolute","unit":"bytes","recipe_name":"python","description":"Resident Memory Usage","recipe_url":"http:\/\/dash.fiveruns.com"},
        {"name":"pmem","data_type":"percentage","recipe_name":"python","description":"Resident Memory Usage","recipe_url":"http:\/\/dash.fiveruns.com"},
        {"name":"cpu","data_type":"percentage","recipe_name":"python","description":"CPU Usage","recipe_url":"http:\/\/dash.fiveruns.com"},
        {"name":"response_time","data_type":"time","recipe_name":"django","description":"Response Time","recipe_url":"http:\/\/dash.fiveruns.com"},
        {"name":"requests","data_type":"counter","recipe_name":"django","description":"Requests","recipe_url":"http:\/\/dash.fiveruns.com"},
        {"name":"render_time","data_type":"time","recipe_name":"django","description":"Render Time","recipe_url":"http:\/\/dash.fiveruns.com"}
      ],
      "recipes":[
        {"name":"python","url":"http:\/\/dash.fiveruns.com"},
        {"name":"django","url":"http:\/\/dash.fiveruns.com"}
      ]
    }
  
  Additional params (TODO, from Ruby):
  
    :type => 'info',
    :ip => Fiveruns::Dash.host.ip_address,
    :mac => Fiveruns::Dash.host.mac_address,
    :hostname => Fiveruns::Dash.host.hostname,
    :pid => Process.pid,
    :os_name => Fiveruns::Dash.host.os_name,
    :os_version => Fiveruns::Dash.host.os_version,
    :pwd => Dir.pwd,
    :arch => Fiveruns::Dash.host.architecture,
    :dash_version => Fiveruns::Dash::Version::STRING,
    :ruby_version => RUBY_VERSION,
    :started_at => @started_at
    :scm_revision => scm.revision,
    :scm_time => scm.time,
    :scm_type => scm.class.scm_type,
    :scm_url => scm.url
    
  """
  
  def path(self):
    return "/apps/%s/processes.json" % self.config.app_token
      
  def _extract_data(self):
    metric_infos = [m.metadata() for m in self.config.metrics.values()]
    recipes = []
    for info in metric_infos:
      key = {"name": info["recipe_name"], "url": info["recipe_url"]}
      if all(v is None for v in key.values()): continue
      if not key in recipes: recipes.append(key)
    return {"metric_infos" : metric_infos, "recipes" : recipes}
    
  def _succeeded(self, body):
    Payload._succeeded(self, body)
    json = simplejson.loads(body)
    self.config.process_id = json['process_id']
    for metric in json['metric_infos']:
      for local_metric in self.config.metrics.values():
        metadata = local_metric.metadata()
        if metric['name'] == metadata['name'] and metric['recipe_name'] == metadata['recipe_name'] and metric['recipe_url'] == metadata['recipe_url']:
          log(metric['id'])
          local_metric.info_id = metric['id']
          break    
  
class DataPayload(Payload):
  """
  Sample data structure:
    [
      {"metric_info_id":932254178,"values":[{"value":68616,"context":null}]},
      {"metric_info_id":932254179,"values":[{"value":3.3,"context":null}]},
      {"metric_info_id":932254180,"values":[{"value":13.2991273667512,"context":null}]},
      {"metric_info_id":932254181,"values":[]},{"metric_info_id":932254182,"values":[]},
      {"metric_info_id":932254183,"values":[{"value":0,"context":null}]},
      {"metric_info_id":932254184,"values":[]},
      {"metric_info_id":932254185,"values":[{"value":0,"context":null}]},
      {"metric_info_id":932254186,"values":[{"value":0,"context":null}]},
      {"metric_info_id":932254187,"values":[{"value":0,"context":null}]},
      {"metric_info_id":932254188,"values":[]}
    ]
  """
  
  def path(self):
    return "/apps/%s/metrics.json" % self.config.app_token
    
  def _extract_data(self):
    return [{"metric_info_id": m.info_id, "values": m.values()} for m in self.config.metrics.values()]
    
class PingPayload(Payload):  
  def path(self): return "/apps/%s/ping" % self.config.app_token
  
class TracePayload(Payload):  
  def path(self): return "/apps/%s/traces.json" % self.config.app_token
  
class ExceptionsPayload(Payload):  
  def path(self): return "/apps/%s/exceptions" % self.config.app_token
  
class Reporter(Thread):
  
  def __init__(self, config):
    self.config = config
    self.interval = config.report_interval
    self.tick = 1
    self.stop_requested = False
    self.reported_info = False
    Thread.__init__(self)
    
  def stop(self, *args, **kwargs):
    log("Shutting down...")
    self.stop_requested = True
  
  def run(self):
    self._report_info()
    self.last_report = time.time()
    while not self.stop_requested:
      time.sleep(self.tick)
      if self.stop_requested: break 
      if self._is_ready():
        self._report_data()
    log("Shut down")
          
  def _is_ready(self):
    return time.time() - self.last_report > self.interval
    
  def _report_info(self):
    info = InfoPayload(self.config)
    log("Sending InfoPayload...")
    self.reported_info = info.send()
    return self.reported_info

  def _report_data(self):
    self.last_report = time.time()
    data = DataPayload(self.config)
    if self.reported_info or self._report_info():
      log("Sending DataPayload...")
      return data.send()
    else:
      log("Discarding data for this interval.")
      return False

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
    self.recipe_name = options.get('recipe_name', None)
    self.recipe_url = options.get('recipe_url', None)
    self.lock = RLock()
    self._validate()
    
  def values(self):
    return self._snapshot()
    
  def metadata(self):
    result = {}
    for field in ['name', 'unit', 'description', 'recipe_name', 'recipe_url']:
      result[field] = self.__dict__[field]
    result['data_type'] = self._data_type()
    return result
            
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

def post_multipart(host, selector, fields, files):
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTPConnection(host)
    headers = {'User-Agent': 'Python','Content-Type': content_type}
    try:
      h.request('POST', selector, body, headers)
    except:
      return [False, sys.exc_info()[1], None]      
    res = h.getresponse()
    return res.status, res.reason, res.read()
    
def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
def log(text):
  print "[FiveRuns Dash] %s" % text  

