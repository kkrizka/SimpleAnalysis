from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
import numpy
from ROOT import *

# A simple analysis class that creates a TTree with branches defined by different
# Variables, and fills it for each event. The TTree is called 'tree' and is saved
# inside a ROOT file called 'output.root', located in the results directory.
#
# The supported variable types right now are int, float, std::vector<int> and
# std::vector<float>.
#
# The variables to be calculated should be set in the member attribute 'variables'
class TreeMakerAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.variables=[]
        
        self.data=[]
        self.fh=None
        self.tree=None

    def init(self):
        self.fh=OutputFactory.getTFile()

        # Create the tree, branches and variable pointers
        self.tree=TTree('tree','tree')
        
        for var in self.variables:
            var.branch_type=None
            if type(var.type)==tuple:
                if var.type[0]==list:
                    if var.type[1]==float:
                        var.pointer=std.vector('float')()
                    elif var.type[1]==int:
                        var.pointer=std.vector('int')()
                    else:
                        var.pointer=std.vector(var.type[1].__name__)()
            else:
                if var.type==float:
                    var.branch_type='%s/D'%var.name
                    var.pointer=numpy.zeros(1,dtype=var.type)
                elif var.type==int:
                    var.branch_type='%s/I'%var.name
                    var.pointer=numpy.zeros(1,dtype=var.type)
                elif var.type==TVector3:
                    var.pointer=TVector3()

        for var in self.variables:
            if var.branch_type!=None:
                self.tree.Branch(var.name,var.pointer,var.branch_type)
            else:
                self.tree.Branch(var.name,var.pointer)

    def run_event(self):
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
            else:
                var.pointer[0]=value
                    
        self.tree.Fill()
