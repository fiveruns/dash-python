from setuptools import setup, find_packages
#import fiveruns.dash.version

setup(
  name = "fiveruns.dash",
  version = "0.4",
  description = "FiveRuns Dash base library for Python",
  author = "FiveRuns Development Team",
  author_email = "dev@fiveruns.com",
  url = "http://dash.fiveruns.com",
  packages = find_packages('src', exclude = "tests"),
  package_dir = {'': 'src'},
  install_requires = ['simplejson'],
  license = 'MIT',
  namespace_packages = ['fiveruns'],
  extras_require = {
    'git': ['GitPython'],
    'examples':  ["Twisted"],
    'test': ['Mock']
  },
  keywords = "monitoring performance production metrics logging"
)
