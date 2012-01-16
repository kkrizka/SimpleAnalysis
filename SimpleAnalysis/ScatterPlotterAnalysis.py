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

    def init_eventfile(self,event_file):
        self.count=0 # Null the count for the new graph
        # Prepare the graph for each of the variables for this event
        # file
        for variable in self.variables:
            # Histogram for this file
            g=TGraph()
            g.SetMarkerColor(event_file.color)
            g.SetTitle(event_file.title)
            self.multigraph_store[variable].Add(g,'p')
            self.file_count+=1
            self.graph_store[variable]=g

    def event(self,particles):
        self.count+=1
        for variable in self.variables:
            self.graph_store[variable].SetPoint(self.count,variable[0].value(),variable[1].value())

    def deinit_eventfile(self,event_file):
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
            self.multigraph_store[variable].GetYaxis().SetTitle(variable[1].title)

            if self.file_count>1:
                l=c.BuildLegend(.65,.65,.95,.95)
                self.store(l)
                l.Draw()

            c.Update()
            c.SaveAs("%s.png"%name)

        

