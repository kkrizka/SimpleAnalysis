import Analysis
import OutputFactory

from ROOT import *

# This analysis takes in a list of events and outputs all of them into a new
# file inside the results directory. This can be used to trim an existing tree,
# since only the processed events (aka ones that pass a cut) are saved.
#
# The name of the output file is the value of eventfile.outfile (output.root by default)

class TrimAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.outfile=None
        self.outtree=None

    def init(self):
        pass

    def init_eventfile(self):
        # Prepare the output stuff
        if hasattr(self.eventfile,'outfile'):
            self.outfile=OutputFactory.getTFile(self.eventfile.outfile)
        
        # Create a new tree
        self.outtree=self.eventfile.tree.CloneTree(0)
        self.outtree.SetName(self.eventfile.tree.GetName())
        self.outtree.SetTitle(self.eventfile.tree.GetTitle())
        self.eventfile.tree.CopyAddresses(self.outtree)

    def run_event(self):
        self.outtree.Fill()

    def deinit_eventfile(self):
        self.outtree.Write()

    def deinit(self):
        pass
        

