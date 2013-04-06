from ROOT import *
from array import array

## This is a simple library that given a type returns a pointer that can be attached to a TTree branch. It is assumed that
## the user understands int/float objects are actually numpy arrays where the first element is the value of the branch.
##
## Currently the following types are supported:
##  int - array of size 1, typecode=i
##  float - array of size 1, typecode=f
##  bool - array of size 1, typecode=i

def get(type):
    pointer=None
    if type in [int,float,bool]:
        pointer=array(get_typecode(type),[0])
    elif type.__name__[0:6]=='vector':
        pointer=type()
    return pointer

## Returns the code for a python type, None is not supported.
def get_typecode(type):
    if type==int or type==bool:
        return 'i'
    elif type==float:
        return 'f'
    return None
