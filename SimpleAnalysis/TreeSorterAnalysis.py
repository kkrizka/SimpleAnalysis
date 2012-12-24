from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
from ROOT import *

# A simple analysis class that copies the branches from an input TTree and stores
# the result in an output TTree. The output tree that it stores them inside depends
# on a series of cuts.
#
# The result is stored in the results directory, inside a file named after the
# chain of cuts specified.
class Destination:
    def __init__(self,filename):
        self.filename=filename
        self.cuts=[]

        self.fh=None
        self.tree=None

    def init_eventfile(self,eventfile):
        if self.fh==None:
            self.fh=OutputFactory.getTFile(self.filename)
            self.tree=eventfile.tree.CloneTree(0)

        eventfile.tree.CopyAddresses(self.tree)

    def fill(self,event):
        for cut in self.cuts:
            cut.event=event
            if cut.cut()!=cut.invert: # Do cut
                return
        self.tree.Fill()

    def deinit(self,eventfile):
        if self.fh!=None:
            self.fh.cd()
            self.tree.Write()
            print self.filename,self.tree.GetEntries()
        
        
class TreeSorterAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.destinations=[]

    def init_eventfile(self):
        for destination in self.destinations:
            destination.init_eventfile(self.eventfile)

    def run_event(self):
        for destination in self.destinations:
            destination.fill(self.event.raw)

    def deinit(self):
        for destination in self.destinations:
            destination.deinit(self.eventfile)
