_cache=dict()

_event=None
_eventfile=None
_eventID=None

def setEvent(event):
    global _event
    _event=event
    for key in _cache:
        _cache[key].event=event
        _cache[key].dirty_bit=True


def setEventFile(eventfile):
    global _eventfile
    _eventfile=eventfile
    for key in _cache:
        _cache[key].eventfile=eventfile

def get(variable,*args,**kwargs):
    # Determine the key
    key=str(variable)+str(args)+str(kwargs)
    if key not in _cache:
        _cache[key]=variable(*args)
        _cache[key].event=_event
        _cache[key].eventfile=_eventfile
        # Set the extra keyword args
        for k in kwargs:
            v=kwargs[k]
            setattr(_cache[key],k,v)

    return _cache[key]

