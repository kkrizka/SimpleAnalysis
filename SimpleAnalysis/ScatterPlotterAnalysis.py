import Analysis
from ROOT import *

# This is a general class to run the analysis on a set of simulated events.
# The variables and cuts to be run are configured in the following section.
# It loops over all of the events that pass a cut and makes a scatter plot
# of all defined variable pairs. Each plot consists of several other plots
# stacked on top of each other, with the "other plots" corresponding to the
# different event ROOT files defined. 
#
# The EventFile's need to have a "color" attribute that corresponds to
# the color that will be used to set the drawn colors.

class ScatterPlotterAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.variables=[]
        self.multigraph_store=dict()
        self.graph_store=dict()
        self.count=0
        self.file_count=0

    def init(self):
        # Book multigraphs for all the variable pairs
        for variable in self.variables:
            name='%s_vs_%s'%(variable[1].title,variable[0].title)
            title=''
            mg=TMultiGraph(name,title)
            self.multigraph_store[variable]=mg

    def init_eventfile(self):
        self.count=0 # Null the count for the new graph
        # Prepare the graph for each of the variables for this event
        # file
        for variable in self.variables:
            # Histogram for this file
            g=TGraph()
            g.SetMarkerColor(self.eventfile.color)
            g.SetFillColor(self.eventfile.color)
            g.SetLineColor(self.eventfile.color)
            g.SetTitle(self.eventfile.title)
            self.multigraph_store[variable].Add(g,'p')
            self.file_count+=1
            self.graph_store[variable]=g

    def run_event(self):
        self.count+=1
        for variable in self.variables:
            self.graph_store[variable].SetPoint(self.count,variable[0].value(),variable[1].value())

    def deinit_eventfile(self):
        pass

    def deinit(self):
        # Draw everything
        for variable in self.variables:
            
            name='c1_%s_vs_%s'%(variable[1].__class__.__name__,variable[0].__class__.__name__)
            c=TCanvas(name,name)
            self.store(c)
#            c.SetLogy(True)
            self.multigraph_store[variable].Draw("AP")
            self.multigraph_store[variable].GetXaxis().SetTitle(variable[0].title)
            self.multigraph_store[variable].GetXaxis().SetRangeUser(variable[0].minval,variable[0].maxval)
            self.multigraph_store[variable].GetYaxis().SetTitle(variable[1].title)
            self.multigraph_store[variable].GetYaxis().SetRangeUser(variable[1].minval,variable[1].maxval)

            if self.file_count>1:
                l=c.BuildLegend(.65,.65,.95,.95)
                self.store(l)
                l.Draw()

            c.Update()
            c.SaveAs("%s.eps"%name)

        

