from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
import numpy
from ROOT import *

# A simple analysis class that copies the branches from an input TTree and stores
# the result in an output TTree. This is done only for events that pass a cut.
#
# The result is stored in the results directory, inside a file named same as
# set in eventfile.output (or output.root if the attribute does not exist).
class TreeCopyAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.fh=None
        self.tree=None

    def init_eventfile(self):
        if hasattr(self.eventfile,'output'):
            self.fh=OutputFactory.getTFile(self.eventfile.output)
        else:
            self.fh=OutputFactory.getTFile()

        # Create the output tree
        self.eventfile.tree.SetBranchStatus('*',1)
        self.tree=self.eventfile.tree.CloneTree(0)
        self.eventfile.tree.CopyAddresses(self.tree)

    def run_event(self):
        self.tree.Fill()

    def deinit_eventfile(self):
        self.tree.Write()
