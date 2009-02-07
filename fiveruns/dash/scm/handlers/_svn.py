import logging
import os
import time
from fiveruns.dash.scm import handler

logger = logging.getLogger('fiveruns.dash.scm.handlers.svn')

class Handler(handler.Handler):

    def collect(self):
        self._check_info()
        if not len(self.data):
            return False
        self.data['scm_type'] = 'svn'
        return True

    def _check_info(self):
        try:
            fn = os.popen("svn info '%s'" % self.match)
        except:
            logger.warn("Could not access `svn info,` is `svn` in PATH?")
        mapping = {'URL': 'scm_url', 'Revision': 'scm_revision'}
        for line in fn.readlines():
            pair = [x.strip() for x in line.split(':', 1)]
            if mapping.has_key(pair[0]):
                self.data[mapping[pair[0]]] = pair[1]

def matches(directory):
    matcher = lambda dir, fn: os.path.isdir(os.path.join(dir, '.svn'))
    found = handler.ascend(matcher, directory, '')
    if found:
        return os.path.join(found, '.svn')
