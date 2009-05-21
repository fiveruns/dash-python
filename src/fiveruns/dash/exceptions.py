import logging
import sys
import traceback
from StringIO import StringIO

logger = logging.getLogger('fiveruns.dash.exceptions')

class Recorder:

    def __init__(self, session):
        self.session = session
        self.data = {}

    def record(self, info, sample = {}):
        exc = self._extract(info)
        key = (exc['name'], exc['backtrace'])
        if key in self.data:
            self.data[key]['total'] += 1
        else:
            exc.update({"total": 1, "sample": self._flatten(sample)})
            self.data[key] = exc
        logger.debug("Recorded exception: %s" % self.data[key])

    def _extract(self, info):
        backtrace = StringIO()
        traceback.print_exc(file=backtrace)
        extraction = {
            "name": type(info).__name__,
            "message": "\n".join(info.args),
            "backtrace":  backtrace.getvalue()
        }
        backtrace.close()
        return extraction

    def _flatten(self, sample):
        return dict([(str(k), str(v)) for k, v in sample.iteritems()])
