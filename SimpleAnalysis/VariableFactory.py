from SimpleAnalysis import Analysis
import traceback
import sys

_cache=dict()

def get(variable,*args,**kwargs):
    return CachedVariable(variable,*args,**kwargs)

##
# A special variable that wraps around another variable and caches its value.
#
# It is also possible to define a variable weight, through the weight attribute. This
# weight is then added to the returned value by formatting it as a tuple. The weight
# is another variable that returns either a single value or a list. In the case of a
# single value, the same weight is set for all of the values returned by a variable. If
# it is a list, then the index of the weight list is matched to the index of the value
# list.
#
# To obtain the list of values with their weights, use the wvalue() function. The weights
# are appended to the values as a second entry in the tuple. The first entry is the
# value.
#
# The following attributes are optional:
# - weight: A Variable object that returns the weight for the event.
class CachedVariable(Analysis.Variable):
    # Arguments:
    #  variable: The variable class that one wants to cache
    #  *args: Arguments to pass to the variable constructor
    #  *kwargs: Member attributes to set after the variable has been created. Ones starting with _ are
    #           set to the CachedVariable only (ie: not used for determining uniqness)
    def __init__(self,variable,*args,**kwargs):
        # Remove hidden arguments from kwargs
        hiddenargs={}
        allargs={}
        for key,value in kwargs.items():
            if key[0]=='_': #hidden
                hiddenargs[key[1:]]=value
                allargs[key[1:]]=value
            else:
                allargs[key]=value
        for key,value in hiddenargs.items():
            del kwargs['_'+key]

        # Determine the key
        key=str(variable)+str(args)+str(kwargs)

        # Make if not exists
        if key not in _cache:
            _cache[key]=variable(*args)

            # setup the cache
            _cache[key].cached_value=None
            _cache[key].cached_eventfile=None
            _cache[key].cached_eventidx=None

            # Set the extra keyword args
            for k,v in kwargs.items():
                v=kwargs[k]
                setattr(_cache[key],k,v)
                
        # Setup this class
        self.variable=_cache[key]
        Analysis.Variable.__init__(self,self.variable.name,self.variable.type)
        for k,v in allargs.items():
            setattr(self,k,v)


    # Access to members of this variable
    def __getattr__(self,attr):
        #print self.variable,attr,'__GETATTR__'
        #traceback.print_stack(file=sys.stdout)
        if attr[0:2]=='__' and attr[-2:]=='__': raise AttributeError
        return getattr(self.variable,attr)

    # The value returned by this variable, with cache lookup.
    def value(self):
        if self.eventfile.eventidx!=self.variable.cached_eventidx or self.eventfile!=self.variable.cached_eventfile:
            self.variable.cached_value=self.variable.value()
            self.variable.cached_eventfile=self.eventfile
            self.variable.cached_eventidx=self.eventfile.eventidx

        return self.variable.cached_value

    # The value of this variable, along with the weight.
    def wvalue(self):
        values=self.value()
        if values==None: return None
        
        # Apply weighting, if necessary
        wvalues=None
        weights=self.weight.value() if self.weight!=None else 1

        values=[values] if type(values)!=list else values
        weights=[weights]*len(values) if type(weights)!=list else weights

        wvalues=zip(values,weights)
        return wvalues[0] if len(wvalues)==1 else wvalues
