from setuptools import setup, find_packages
import fiveruns_dash

setup(
  name = "fiveruns_dash",
  version = ".".join(str(s) for s in fiveruns_dash.version_info),
  description = "Base Python client for FiveRuns Dash service",
  author = "FiveRuns Development Team",
  author_email = "dev@fiveruns.com",
  url = "http://dash.fiveruns.com",
  packages = find_packages(exclude = "tests"),
  install_requires = ['Twisted', 'python-aspects>=1.3']
)
