import Analysis

from ROOT import *
import tempfile
from math import *

### This file contains a few Variable/Cut/EventFile classes that are common to many
### analysis chains.

## Event Files ##

## A event file where the tree is first pruned using a generic ROOT selection
## via CopyTree.
## Extra attributes:
##  selection: The selection that will be used when pruning the tree
##  fullTree: The complete, unpruned tree
##  fh_tmp: The temporary ROOT file used to store the pruned tree
class EventFileWithSelection(Analysis.EventFile):
    def __init__(self,path,treeName,selection):
        Analysis.EventFile.__init__(self,path,treeName)
        self.selection=selection

    def load_tree(self):
        self.fh=TFile.Open(self.path)
        if self.fh.FindKey(self.treeName)==None:
            return False
        self.fullTree=self.fh.Get(self.treeName)

        # Need temporary storage for large trees
        self.tmpdir=tempfile.mkdtemp()
        self.fh_tmp=TFile('%s/tmp.root'%self.tmpdir,'RECREATE')
        self.tree=self.fullTree.CopyTree(self.selection)
        return True

    def close(self):
        self.fh.Close()
        self.fh_tmp.Close()
        
        
### Cuts ###

## A generic cut that uses any variable and rejects events that have the
## variable value less than minVal.
class VariableCut(Analysis.Cut):
    ## Arguments:
    ## - variable: An Analysis.Variable object that cuts will be run on
    ## - minVal: The minimum value of the variable below which events are 
    ##           rejected.
    ## - invert: Boolean indicating whether the cut should be inverted.
    ##           Inverted cuts reject events with values above minVal.
    ##           (Default: False)
    def __init__(self,variable,minVal,invert=False):
        Analysis.Cut.__init__(self,invert)
        self.variable=variable
        self.minVal=minVal

    ## Cut method
    def cut(self):
        value=self.variable.value()
        if(value<self.minVal):
            return True
        return False

## A generic cut that uses any variable and rejects events that have the
## variable equal to zero.
class VariableFlagCut(Analysis.Cut):
    ## Arguments:
    ## - variable: An Analysis.Variable object that cuts will be run on
    ## - invert: Boolean indicating whether the cut should be inverted.
    ##           Inverted cuts reject events with values not equal to zero.
    ##           (Default: False)
    def __init__(self,variable,invert=False):
        Analysis.Cut.__init__(self,invert)
        self.variable=variable

    ## Cut method
    def cut(self):
        value=self.variable.value()
        if value==0: return True
        else: return False


### Variables ###
## Sum of different variables
class Sum(Analysis.Variable):
    def __init__(self,variables):
        titles=[]
        minval=0
        maxval=0
        for variable in variables:
            titles.append(variable.title)
            minval+=variable.minval
            maxval+=variable.maxval
        title=' + '.join(titles)
        Analysis.Variable.__init__(self,title)
        self.nbins=100
        self.minval=minval
        self.maxval=maxval

        self.variables=variables
        
    def value(self):
        value=0
        for variable in self.variables:
            value+=variable.value()
        return value

## Returns a value from a branch
class RawBranchVariable(Analysis.Variable):
    def __init__(self,branch_name,type):
        Analysis.Variable.__init__(self,branch_name,type)
        self.branch_name=branch_name

    def calculate(self):
        return self.event.raw.__getattr__(self.branch_name)
