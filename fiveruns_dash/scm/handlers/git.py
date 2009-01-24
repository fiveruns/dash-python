import os, logging
from fiveruns_dash.scm import handler

class Handler(handler.Handler):

  def collect(self):
    git = self._import()
    if not git: return False
    repo = git.Repo.init_bare(self.match)
    # TODO: Collect info and add to ``self.data``
    return True

  # TODO: Graceful
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
