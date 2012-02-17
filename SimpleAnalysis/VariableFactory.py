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
    key=str(variable)+str(args)
    if(key not in _cache):
        _cache[key]=variable(*args)
        _cache[key].name=_cache[key].name+str(args)
        _cache[key].particles=_particles
        _cache[key].eventID=_eventID

    return _cache[key]

