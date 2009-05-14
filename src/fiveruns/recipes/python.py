import fiveruns
import os
import gc

python_recipe = fiveruns.dash.recipe('python', 'http://dash.fiveruns.com')

def _vsz():
    print "_vsz"
    vmem_idx = 1
    pipe = os.popen('/bin/ps -o vsz -p %s' % str(os.getpid()))
    vmem = int(pipe.read().split()[vmem_idx])
    pipe.close()
    return vmem

def _rss():
    print "_rss"
    rss_idx = 1
    pipe = os.popen('/bin/ps -o rss -p %s' % str(os.getpid()))
    rss = int(pipe.read().split()[rss_idx])
    pipe.close()
    return rss

def _pmem():
    print '_pmem'
    pmem_idx = 1
    pipe = os.popen('/bin/ps -o pmem -p %s' % str(os.getpid()))
    pmem = float(pipe.read().split()[pmem_idx])
    pipe.close()
    return pmem

#TODO: Pretty sure the calc below will not work. Fix it
#def _cpu():
#    if not '_cpu_before' in globals():
#        global _cpu_before
#        _cpu_before = os.times()[0]
#
#    cpu_after = os.times()[0]
#    this_minute = cpu_after - _cpu_before
#    _cpu_before = cpu_after
#
#    return (this_minute / 60.0) * 100.00

def _refcount():
    ''' Get number of system refcounts total. '''
    print "_refcount"
    return len(gc.get_objects())


python_recipe.absolute('vsz', 'Virtual Memory Usage', unit = 'kbytes', call = _vsz)
python_recipe.absolute('rss', 'Resident Memory Usage', unit = 'kbytes', call = _rss)
python_recipe.percentage('pmem', 'Percentage Resident Memory Usage', call = _pmem)
#python_recipe.percentage('cpu', 'Percentage CPU Usage', call = _cpu)
python_recipe.absolute("gc_objects", "Number of GC tracked objects", call=_refcount)

