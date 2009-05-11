from setuptools import setup, find_packages
#import fiveruns.dash.version

setup(
  name = "fiveruns.dash",
  #I like the idea for getting the version this way, but hard to do after moving the fiveruns module into src/
  #version = ".".join(str(s) for s in fiveruns.dash.version.info),
  version = "0.3.2",
  description = "FiveRuns Dash base library for Python",
  author = "FiveRuns Development Team",
  author_email = "dev@fiveruns.com",
  url = "http://dash.fiveruns.com",
  packages = find_packages('src', exclude = "tests"),
  package_dir = {'': 'src'},
  install_requires = ['simplejson', 'python-aspects >= 1.3'],
  license = 'MIT',
  dependency_links = [
    # Pypi only has python-aspects-1.1 as of 2009-01-19, need 1.3
    'http://www.cs.tut.fi/~ask/aspects/python-aspects-1.3.tar.gz'
  ],
  namespace_packages = ['fiveruns'],
  extras_require = {
    'git': ['GitPython'],
    'examples':  ["Twisted"],
    'test': ['Mock']
  },
  keywords = "monitoring performance production metrics logging"
)
