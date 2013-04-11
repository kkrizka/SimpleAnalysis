import Analysis

from ROOT import *
import tempfile, os
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
        os.remove('%s/tmp.root'%self.tmpdir)


## A event file that is a TChain of ROOT files
class EventFileChain(Analysis.EventFile):
    def __init__(self,paths,treeName):
        Analysis.EventFile.__init__(self,paths,treeName)

    def load_tree(self):
        self.tree=TChain(self.treeName)
        
        for path in self.path:
            self.tree.Add(path)

        return True

    def close(self):
        pass
        
        
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
## variable different from some value
class VariableEqualCut(Analysis.Cut):
    ## Arguments:
    ## - variable: An Analysis.Variable object that cuts will be run on
    ## - val: The value that we require to be equal
    ## - invert: Boolean indicating whether the cut should be inverted.
    ##           Inverted cuts reject events with values not equal to val.
    ##           (Default: False)
    def __init__(self,variable,val,invert=False):
        Analysis.Cut.__init__(self,invert)
        self.variable=variable
        self.val=val

    ## Cut method
    def cut(self):
        value=self.variable.value()
        if value!=self.val: return True
        else: return False

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
## Returns a constant value
class ConstantVariable(Analysis.Variable):
    def __init__(self,x,type=float):
        Analysis.Variable.__init__(self,'constant_%s'%str(x),type)
        self.x=x
        
    def calculate(self):
        return self.x

        
## Sum of different variables
class SumVariable(Analysis.Variable):
    def __init__(self,variables):
        Analysis.Variable.__init__(self,'sum_%s'%str(variables),variables[0].type)
        self.variables=variables
        
    def calculate(self):
        value=0
        for variable in self.variables:
            value+=variable.value()
        return value

## Product of different variables
# All must be of the same type
# If type is list, product is taken element wise
class ProductVariable(Analysis.Variable):
    def __init__(self,variables):
        # Determine type by looking at the first type, then check if it will become a list at some time later
        t=variables[0].type
        for variable in variables:
            if type(variable.type)==tuple:
                t=variable.type
                
        Analysis.Variable.__init__(self,'product_%s'%str(variables),t)
        self.variables=variables
        
    def calculate(self):
        value=1
        for variable in self.variables:
            value=self.multiply(value,variable.value())
        return value


    def multiply(self,value1,value2):
        if type(value1)!=list and type(value2)!=list:
            return value1*value2
        if type(value1)!=list and type(value2)==list:
            for i in range(len(value2)):
                value2[i]*=value1
            return value2
        if type(value1)==list and type(value2)!=list:
            for i in range(len(value1)):
                value1[i]*=value2
            return value1
        if type(value1)==list and type(value2)==list:
            for i in range(len(value1)):
                value1[i]*=value2[i]
            return value1

## Returns a value from a branch
class RawBranchVariable(Analysis.Variable):
    def __init__(self,branch_name,type=float):
        Analysis.Variable.__init__(self,branch_name,type)
        self.branch_name=branch_name
        
    def calculate(self):
        if type(self.type)==tuple and self.type[0]==list:
            return list(self.event.__getattr__(self.branch_name))
        elif self.type==str:
            return str(self.event.__getattr__(self.branch_name))
        else:
            return self.event.__getattr__(self.branch_name)
