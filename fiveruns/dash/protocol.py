import httplib
import logging
import mimetypes
import os
import sys
import urlparse
import zlib
from socket import gethostname

import simplejson
import scm

logger = logging.getLogger('fiveruns.dash.protocol')

connections = {'http': httplib.HTTPConnection, 'https': httplib.HTTPSConnection}

class Payload(object):

    def __init__(self, config):
        self.config = config
        self.data = self._extract_data()

    def send(self):
        if not self.valid():
            logger.error("Invalid payload format")
            logger.debug(self.data)
            return False
        logger.debug("Sending to %s%s\n%s", self.url(), self.path(), self.data)
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
        if 'DASH_UPDATE' in os.environ:
            return os.environ['DASH_UPDATE']
        else:
            return 'https://dash-collector.fiveruns.com'

    def valid(self):
        if hasattr(self.__class__, 'validations'):
            for validation in self._class__.validations:
                if not validation(self):
                    return False
        return True

    def _succeeded(self, body):
        logger.debug("Succeeded.")

    def _failed(self, reason):
        logger.debug("Failed (%s)" % reason)

    def _unknown(self, status, reason):
        logger.debug("Unknown error (%s, %s)" % (status, reason))

    def _extra_params(self):
        return [
          ('hostname', gethostname()),
          ('app_id', self.config.app_token),
          ('ip', '127.0.0.1'), # FIXME
          ('pid', str(self.config.pid)),
          ('pwd', self.config.pwd),
          ('vm_version', self.config.vm_version),
          ('process_id', self.config.process_id and str(self.config.process_id) or ''),
        ]

    def _compressed(self):
        return zlib.compress(self._serialize())

    def _serialize(self):
        return simplejson.dumps(self.data)


class InfoPayload(Payload):

    def path(self):
        return "/apps/%s/processes.json" % self.config.app_token

    def _extract_data(self):
        metric_infos = [m.metadata() for m in self.config.metrics.values()]
        recipes = []
        for info in metric_infos:
            key = {"name": info["recipe_name"], "url": info["recipe_url"]}
            if all(v is None for v in key.values()): continue
            if not key in recipes: recipes.append(key)
        data = {"metric_infos" : metric_infos, "recipes" : recipes}
        data.update(self.config.extra_payload_data.get('info', {}))
        return data

    def _extra_params(self):
        params = super(InfoPayload, self)._extra_params()
        return params + self._scm_data()

    def _scm_data(self):
        handler = scm.at(self.config.pwd)
        if handler:
            return dict(handler).items()
        else:
            return []

    def _succeeded(self, body):
        Payload._succeeded(self, body)
        # json = simplejson.loads(body)
        # self.config.process_id = json['process_id']
        # for metric in json['metric_infos']:
        #   for local_metric in self.config.metrics.values():
        #     metadata = local_metric.metadata()
        #     if metric['name'] == metadata['name'] and metric['recipe_name'] == metadata['recipe_name'] and metric['recipe_url'] == metadata['recipe_url']:
        #       logger.debug(metric['id'])
        #       local_metric.info_id = metric['id']
        #       break    

class DataPayload(Payload):

    def path(self):
        return "/apps/%s/metrics.json" % self.config.app_token

    def _extract_data(self):
        data = {}
        real_data = {}
        real_metrics = [(name, metric) for name, metric in self.config.metrics.iteritems() if not metric.virtual]
        virtual_metrics = [(name, metric) for name, metric in  self.config.metrics.iteritems() if metric.virtual]
        for name, metric in real_metrics:
            real_data[name] = self._envelope(metric, metric.values())
        for name, metric in virtual_metrics:
            data[name] = self._envelope(metric, metric.calculate(real_data))
        data.update(real_data)
        return data.values()

    def _envelope(self, m, values):
        """
        Metric data and metadata container
        """
        return {
            "name": m.name,
            "help_text": m.help_text,
            "unit": m.unit,
            "data_type": m.data_type,
            "description": m.description,
            "recipe_name": m.recipe_name,
            "recipe_url": m.recipe_url,
            "name": m.name,
            "values": values }

    
class PingPayload(Payload):
    def path(self):
        return "/apps/%s/ping" % self.config.app_token
  
class TracePayload(Payload):
    def path(self):
        return "/apps/%s/traces.json" % self.config.app_token
  
class ExceptionsPayload(Payload):
    def path(self):
        return "/apps/%s/exceptions" % self.config.app_token
  
def send(urlparts, selector, fields, files):
    content_type, body = encode(fields, files)
    connector = connections[urlparts.scheme]
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
