import Analysis
from ROOT import *

# This analysis takes in a list of events and outputs all of them into a new
# file (opened with RECREATE) and a new tree. This can be used to trim an
# existing tree, since only the processed events (aka ones that pass a cut)
# are saved.
#
# The EventFile's need to have a "outTreeName" and "outFileName" attributes that
# define the name of the output tree and the name of the output file.

class TrimAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.outfile=None
        self.outtree=None

    def init(self):
        pass

    def init_eventfile(self):
        # Prepare the output stuff
        self.outfile=TFile(self.eventfile.outFileName,"UPDATE")
        
        # Delete any existing trees in the file, if exists
        self.outfile.Delete("%s;*"%self.eventfile.outTreeName)
        self.outfile.cd()

        # Create a new tree
        self.outtree=self.eventfile.tree.CloneTree(0)
        self.outtree.SetName(self.eventfile.outTreeName)
        self.outtree.SetTitle(self.eventfile.outTreeName)
        self.eventfile.tree.CopyAddresses(self.outtree)

    def run_event(self):
        self.outtree.Fill()

    def deinit_eventfile(self):
        self.outtree.Write()
        self.outfile.Close()

    def deinit(self):
        pass
        

