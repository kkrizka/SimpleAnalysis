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

    def init_eventfile(self,event_file):
        # Prepare the output stuff
        self.outfile=TFile(event_file.outFileName,"RECREATE")
        
        self.outtree=TTree(event_file.outTreeName,event_file.outTreeName)
        self.outtree.Branch("particle",self.particles);

    def event(self,particles):
        self.outtree.Fill()

    def deinit_eventfile(self,event_file):
        self.outtree.Write()
        self.outfile.Close()

    def deinit(self):
        pass
        

