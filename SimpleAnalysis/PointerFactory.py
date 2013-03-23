from ROOT import *
import numpy as np

## This is a simple library that given a type returns a pointer that can be attached to a TTree branch. It is assumed that
## the user understands int/float objects are actually numpy arrays where the first element is the value of the branch.
##
## Currently the following types are supported:
##  int - numpy array of size 1, dtype=int
##  float - numpy array of size 1, dtype=float
##  bool - numpy array of size 1, dtype=bool

def get(type):
    pointer=None
    if type in [int,float,bool]:
        pointer=np.zeros(1,dtype=type)
    elif type.__name__[0:6]=='vector':
        pointer=type()
    return pointer
