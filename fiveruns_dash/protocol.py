import os, sys, httplib, mimetypes, simplejson, urlparse, zlib
from socket import gethostname

from logging import log

CONNECTIONS = {'http': httplib.HTTPConnection, 'https': httplib.HTTPSConnection}

class Payload(object):
  
  def __init__(self, config):
    self.config = config
    self.data = self._extract_data()
        
  def send(self):
    urlparts = urlparse.urlparse(self.url())
    (status, reason, body) = send(
      urlparts,
      self.path(),
      self._extra_params(),
      [('file', 'data.json.gz', self._compressed())]
    )
    if status == 201:
      self._succeeded(body)
      return True
    elif status in range(400, 499):
      print body
      self._failed(reason)
    else:
      print body
      self._unknown(status, reason)
    return False # TODO: HTTP
    
  def url(self):
    if os.environ.has_key('DASH_UPDATE'):
      return os.environ['DASH_UPDATE']
    else:
      return 'https://dash-collector.fiveruns.com'
  
  def _succeeded(self, body):
    log("Succeeded.")
    
  def _failed(self, reason):
    log("Failed (%s)" % reason)
  
  def _unknown(self, status, reason):
    log("Unknown error (%s, %s)" % (status, reason))
    
  def _extra_params(self):
    return [
      ('hostname', gethostname()),
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
    # json = simplejson.loads(body)
    # self.config.process_id = json['process_id']
    # for metric in json['metric_infos']:
    #   for local_metric in self.config.metrics.values():
    #     metadata = local_metric.metadata()
    #     if metric['name'] == metadata['name'] and metric['recipe_name'] == metadata['recipe_name'] and metric['recipe_url'] == metadata['recipe_url']:
    #       log(metric['id'])
    #       local_metric.info_id = metric['id']
    #       break    
  
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
    
    CHANGED TO:
    
    [
        {
          "name": "vsz",
          "help_text": "The amount of virtual memory used by this process",
          "unit": "kbytes",
          "data_type": "absolute",
          "description": "Virtual Memory Usage",
          "values": [
            {
              "value": 632280,
              "context": null
            }
          ],
          "recipe_name": "ruby",
          "recipe_url": "http:\/\/dash.fiveruns.com/recipes/ruby"
        }
      ]
  """
  
  def path(self):
    return "/apps/%s/metrics.json" % self.config.app_token
    
  def _extract_data(self):
    return [{
      "name": m.name,
      "help_text": m.help_text,
      "unit": m.unit,
      "data_type": m.data_type,
      "description": m.description,
      "recipe_name": m.recipe_name,
      "recipe_url": m.recipe_url,
      "name": m.name,
      "values": m.values()
    } for m in self.config.metrics.values()]
    
class PingPayload(Payload):  
  def path(self): return "/apps/%s/ping" % self.config.app_token
  
class TracePayload(Payload):  
  def path(self): return "/apps/%s/traces.json" % self.config.app_token
  
class ExceptionsPayload(Payload):  
  def path(self): return "/apps/%s/exceptions" % self.config.app_token
  
def send(urlparts, selector, fields, files):
    content_type, body = encode(fields, files)
    connector = CONNECTIONS[urlparts.scheme]
    connection = connector(urlparts.netloc)
    headers = {'User-Agent': 'Python','Content-Type': content_type}
    try:
      connection.request('POST', selector, body, headers)
    except:
      return [False, sys.exc_info()[1], None]      
    res = connection.getresponse()
    return res.status, res.reason, res.read()
    
def encode(fields, files):
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
        L.append('Content-Type: %s' % _content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def _content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
  
