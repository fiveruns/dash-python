import logging
import sys
import traceback

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
        return {
            "name": type(info).__name__,
            "message": "\n".join(info.args),
            "backtrace": "Tracebacks are not currently supported for Python"
        }

    def _flatten(self, sample):
        return dict((str(k), str(v)) for k, v in sample.iteritems())
