from ROOT import *
import os,os.path
import glob
import datetime
import atexit

_name=None # Name where the results directory will be.
_resultsdir=None # The path to the results directory, when created.
_tfiles={} # A dictionary of opened TFiles. The key is the full path to the ROOT file.

# Returns a path to the results directory, and creates it if it does not
# exist already.
def results():
    global _name, _resultsdir
    if _resultsdir!=None:
        return _resultsdir

    # Create the directory structure
    resultsdir=os.path.join(os.getcwd(), 'results',_name)

    now = datetime.datetime.now()
    existing=glob.glob(os.path.join(resultsdir,'%d%02d%02d-[0-9]*'%(now.year,now.month,now.day)))
    idx="%03d"%(len(existing)+1)
    
    resultsdir=os.path.join(resultsdir,'%d%02d%02d-%s'%(now.year,now.month,now.day,idx))

    if not os.path.isdir(resultsdir):
        os.makedirs(resultsdir)

    _resultsdir=resultsdir

    return _resultsdir

# Returns a pointer to a TFile named "name" inside the results directory
#  name - The name of the output ROOT file. 'output.root' by default.
def getTFile(name='output.root'):
    global _tfiles

    path=os.path.join(results(),name)
    if path in _tfiles:
        return _tfiles[path]

    f=TFile(path,'CREATE')
    _tfiles[path]=f
    return f

# Set the output name. Used by results() to determine the name of the
# results directory. Should never be called manually!
def setOutputName(name):
    global _name
    _name=name

# Set the results directory. It is created if it does not exist. If set to
# none, it is calculated automatically on the first call to results().
# Should never be called manually!
def setResults(resultsdir):
    global _resultsdir
    _resultsdir=resultsdir

    if resultsdir==None: return
    
    if not os.path.isdir(_resultsdir):
        os.makedirs(_resultsdir)

# Closes all the stale file handles and prints out the output directory. This is called automatically by the code (if a results
# directory was created). Should never be called manually!
def cleanup():
    global _files,_resultsdir
    for file in _tfiles:
        _tfiles[file].Write()
        _tfiles[file].Close()

    if _resultsdir!=None:
        print 'Output stored inside %s'%_resultsdir

# Register an exit function that closes all of the necessary files
atexit.register(cleanup)
