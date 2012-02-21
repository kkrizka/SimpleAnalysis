_cache=dict()

_particles=None
_eventFile=None
_eventID=None

def setParticles(particles):
    _particles=particles
    for key in _cache:
        _cache[key].particles=particles

def setEventFile(eventFile):
    _eventFile=eventFile
    for key in _cache:
        _cache[key].eventFile=eventFile

def setEventID(eventID):
    _eventID=eventID
    for key in _cache:
        _cache[key].eventID=eventID


def get(variable,*args):
    # Build a key for arguments...
    args_key=''
    for arg in args:
        if type(arg)==float or type(arg)==int:
            args_key+=(str(arg)+',')
        elif type(arg)==str:
            args_key+=('"'+str(arg)+'",')
        else:
            args_key+=(arg.__class__.__name__+',')
    if args_key!='':
        args_key=args_key[:-1]

    # Create
    key=str(variable)+str(args)
    if(key not in _cache):
        _cache[key]=variable(*args)
        _cache[key].name=_cache[key].name+'('+args_key+')'
        _cache[key].particles=_particles
        _cache[key].eventID=_eventID

    return _cache[key]

