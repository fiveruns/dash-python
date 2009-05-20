import fiveruns
import os
import gc

python_recipe = fiveruns.dash.recipe('python', 'http://dash.fiveruns.com')

def _vsz():
    vmem_idx = 1
    pipe = os.popen('/bin/ps -o vsz -p %s' % str(os.getpid()))
    vmem = int(pipe.read().split()[vmem_idx])
    pipe.close()
    return vmem
_vsz = python_recipe.absolute('vsz', 'Virtual Memory Usage', unit = 'kbytes')(_vsz)

def _rss():
    rss_idx = 1
    pipe = os.popen('/bin/ps -o rss -p %s' % str(os.getpid()))
    rss = int(pipe.read().split()[rss_idx])
    pipe.close()
    return rss
_rss = python_recipe.absolute('rss', 'Resident Memory Usage', unit = 'kbytes')(_rss)

def _pmem():
    pmem_idx = 1
    pipe = os.popen('/bin/ps -o pmem -p %s' % str(os.getpid()))
    pmem = float(pipe.read().split()[pmem_idx])
    pipe.close()
    return pmem
_pmem = python_recipe.percentage('pmem', 'Percentage Resident Memory Usage')(_pmem)

cpu_before = None
def _cpu():
    global cpu_before
    if not cpu_before:
        cpu_before = os.times()

    cpu_after = os.times()
    
    user_time = cpu_after[0] - cpu_before[0]
    system_time = cpu_after[1] - cpu_before[1]
    cpu_time = user_time + system_time
    cpu_before = cpu_after

    return (system_time / 60.0) * 100.00
_cpu = python_recipe.percentage('cpu', 'Percentage CPU Usage')(_cpu)

def _refcount():
    ''' Get number of system refcounts total. '''
    return len(gc.get_objects())
_refcount = python_recipe.absolute('gc_objects', 'Number of GC tracked objects')(_refcount)
