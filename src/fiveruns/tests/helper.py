import sys
from StringIO import StringIO

saved_stdout = sys.stdout
saved_stdin = sys.stdin

def mock_stdout():
    new_stdout = StringIO()
    sys.stdout = new_stdout
    return new_stdout

def mock_stdin():
    new_stdin = StringIO()
    sys.stdin = new_stdin
    return new_stdin

def mock_streams():
    return mock_stdout(), mock_stdin

def restore_stdout():
    sys.stdout = saved_stdout
    
def restore_stdin():
    sys.stdin = saved_stdin

def restore_streams():
    restore_stdout()
    restore_stdin()
