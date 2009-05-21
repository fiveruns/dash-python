import logging
import os
import time

from fiveruns.dash.scm import handler

logger = logging.getLogger('fiveruns.dash.scm.handlers.git')

class Handler(handler.Handler):

    def collect(self):
        git = self._import()
        if not git:
            return False

        repo = git.Repo(self.match)
        # check to see there are any branch heads at all
        if not repo.heads:
            head = None
        else:
            head = repo.commits('HEAD')

        # either there were no repo heads, or
        # the commit list is empty
        if not head:
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
        f = open(os.path.join(repo.path, 'config'), 'r')
        try:
            for line in f.readlines():
                if found_origin:
                    stripped = line.strip()
                    if stripped.startswith("url ="):
                        return stripped.split('=', 1)[1].strip()
                else:
                    if line.startswith('[remote "origin"]'):
                        found_origin = True
        finally:
            f.close()
        

    def _import(self):
        """Attempt to import GitPython
        """
        try:
            import git_python
            return git_python
        except ImportError:
            try:
                import git
                return git
            except ImportError:
                self.missing('git_python')
                return False

def matches(directory):
    matcher = lambda dir, fn: os.path.isdir(os.path.join(dir, '.git'))
    found = handler.ascend(matcher, directory, '')
    if found:
        return os.path.join(found, '.git')
