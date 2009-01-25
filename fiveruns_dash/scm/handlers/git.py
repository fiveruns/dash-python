from __future__ import with_statement
import os, logging, time
from fiveruns_dash.scm import handler

logger = logging.getLogger('fiveruns_dash.scm.handlers.git')

class Handler(handler.Handler):

    def collect(self):
        git = self._import()
        if not git: return False
        repo = git.Repo.init_bare(self.match)
        head = repo.commits('HEAD')
        if not head or len(head) < 1:
            logger.warn("Could not retrieve Git HEAD info")
            return False
        tip = head[0]
        self.data.update({
          'scm_type': 'git',
          "scm_revision": tip.id,
          "scm_time": str(int(time.mktime(tip.authored_date)))
        })
        scm_url = self._find_origin(repo)
        if scm_url:
            self.data['scm_url'] = scm_url
        # TODO: Collect info and add to ``self.data``
        return True

    def _find_origin(self, repo):
        found_origin = False
        with open(os.path.join(repo.path, 'config'), 'r') as f:
            for line in f.readlines():
                if found_origin:
                    stripped = line.strip()
                    if stripped.startswith("url ="):
                        return stripped.split('=', 1)[1].strip()
                else:
                    if line.startswith('[remote "origin"]'):
                        found_origin = True
        

    def _import(self):
        try:
            import git_python
            return git_python
        except:
            self.missing('git_python')

def matches(directory):
    matcher = lambda dir, fn: os.path.isdir(os.path.join(dir, '.git'))
    found = handler.ascend(matcher, directory, '')
    if found:
        return os.path.join(found, '.git')
