from ROOT import *
from array import array

## This is a simple library that given a type returns a pointer that can be attached to a TTree branch. It is assumed that
## the user understands int/float objects are actually numpy arrays where the first element is the value of the branch.
##
## Currently the following types are supported:
##  UInt_t - array of size 1, typecode=I
##  Int_t - array of size 1, typecode=i
##  Float_t - array of size 1, typecode=f
##  Double_t - array of size 1, typecode=d
##  Bool_t - array of size 1, typecode=I

def get(typename):
    pointer=None
    array_mappings={'UInt_t':'I','Int_t':'i','Float_t':'f','Double_t':'d','Bool_t':'I'}
    if typename in array_mappings:
        pointer=array(array_mappings[typename],[0])
    elif type in [str,std.string]:
        pointer=std.string()
    elif typename[0:6]=='vector':
        pointer=std.__getattr__(typename)()

    return pointer
