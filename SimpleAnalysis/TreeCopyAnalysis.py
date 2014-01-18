from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
from SimpleAnalysis import PointerFactory

from ROOT import *

import os.path

# A simple analysis class that copies the branches from an input TTree and stores
# the result in an output TTree. This is done only for events that pass a cut.
#
# The tree name is copied, unless analysis.treeName is set.
#
# The result is stored in the results directory, inside a file based on the
# following criteria:
#  1) Using eventfile.output, if set
#  2) Using analysis.output, if set
#  3) The name of the input file
class TreeCopyAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.fh=None
        self.tree=None

        self.output=None
        self.treeName=None

        self.variables=[]
        self.branches=[]
        self.trees=[]

    def init(self):
        # Create variable pointers
        for var in self.variables:
            if not hasattr(var,'branchname'):
                var.branchname=var.name

            var.branch_type=None
            if type(var.type)==tuple:
                if var.type[0]==list:
                    if var.type[1]==float:
                        var.pointer=std.vector('float')()
                    elif var.type[1]==int:
                        var.pointer=std.vector('int')()
                    elif var.type[1]==bool:
                        var.pointer=std.vector('bool')()
                    elif var.type[1]==str:
                        var.pointer=std.vector('std::string')()
                    else:
                        var.pointer=std.vector(var.type[1].__name__)()
            else:
                if var.type==float:
                    var.branch_type='%s/D'%var.branchname
                    var.pointer=PointerFactory.get('Double_t')
                elif var.type==int:
                    var.branch_type='%s/I'%var.branchname
                    var.pointer=PointerFactory.get('Int_t')
                elif var.type==bool:
                    var.branch_type='%s/O'%var.branchname
                    var.pointer=PointerFactory.get('Bool_t')
                elif var.type==TVector3:
                    var.pointer=TVector3()
                elif var.type==TVector2:
                    var.pointer=TVector2()
                elif var.type==str:
                    var.pointer=std.string()

    def init_eventfile(self):
        if hasattr(self.eventfile,'output'):
            self.fh=OutputFactory.getTFile(self.eventfile.output)
        elif self.output!=None:
            self.fh=OutputFactory.getTFile(self.output)
        else:
            self.fh=OutputFactory.getTFile(os.path.basename(self.eventfile.path))

        # Copy any additional trees
        for tree in self.trees:
            dirname=os.path.dirname(tree)
            if dirname!='':
                d=self.fh.GetDirectory(dirname)
                if not d:
                    d=self.fh.mkdir(dirname)
            else:
                d=self.fh
            d.cd()
            tin=self.eventfile.fh.Get(tree)
            tout=tin.CloneTree(0)
            tin.CopyAddresses(tout)
            tout.CopyEntries(tout)
            tout.Write()
        self.fh.cd()

        # Create the output tree
        if len(self.branches)==0: self.eventfile.tree.SetBranchStatus('*',1) # copy all branches
        else: # only copy requested branches
            for branch in self.branches:
                self.eventfile.tree.SetBranchStatus(branch,1)
            
        self.tree=self.eventfile.tree.CloneTree(0)
        self.eventfile.tree.CopyAddresses(self.tree)

        if self.treeName!=None: self.tree.SetName(self.treeName)

        # Create branches for new variables
        for var in self.variables:
            if var.branch_type!=None:
                self.tree.Branch(var.branchname,var.pointer,var.branch_type)
            else:
                self.tree.Branch(var.branchname,var.pointer)



    def run_event(self):
        # Update variables
        for var in self.variables:
            value=var.value()
            if type(value)==list:
                var.pointer.clear()
                for val in value:
                    var.pointer.push_back(val)
            elif type(value)==TVector3:
                var.pointer.SetX(value.x())
                var.pointer.SetY(value.y())
                var.pointer.SetZ(value.z())
            elif type(value)==TVector2:
                var.pointer.Set(value.X(),value.Y())
            elif var.type==str:
                var.pointer.replace(0,std.string.npos,value)
            else:
                var.pointer[0]=value

        # Write
        self.tree.Fill()
