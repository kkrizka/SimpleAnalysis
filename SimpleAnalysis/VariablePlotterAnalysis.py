import Analysis
from ROOT import *

# This is a general class to run the analysis on a set of simulated events.
# The variables and cuts to be run are configured in the following section.
# It loops over all of the events that pass a cut and makes a histogram of
# all defined variables. Each histogram consists of several other
# histograms stacked on top of each other, with the "other histograms" 
# corresponding to the different event ROOT files defined.

# The "other histograms" are scaled to have an area corresponding to a
# requested area. Possible choices are:
#  norm_mode: "none" - leave as is, no normalization (Default)
#  norm_mode: "1" - scale to area of one
#  norm_mode: "xsec" - cross-section of event, before any of the cuts are applied.
#
# If the attribute "stack" is set to False,  then the "nostack" option is used to
# draw the histogams. It is set to True by default.
#
# If a variable returns a list of numbers, all of them are added to a histogram
# invididually.
#
# The EventFile's need to have a "color" attribute that corresponds to
# the color that will be used to draw the histogram line.

class VariablePlotterAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.variables=[]
        self.norm_mode='none'
        self.stack=True

    def init(self):
        # Book histograms for all the variables
        for variable in self.variables:
            hs=THStack()
            variable.histogram=hs

    def init_eventfile(self,event_file):
        # Prepare the histograms for each of the variables for this event
        # file
        for variable in self.variables:
            # Histogram for this file
            h=TH1F("%s-%s"%(variable.title,event_file.path),
                   event_file.title,
                   variable.nbins,
                   variable.minval,
                   variable.maxval)
            if hasattr(event_file,'color'):
                h.SetLineColor(event_file.color)
            variable.histogram.Add(h)
            variable.current_histogram=h

    def event(self,particles):
        for variable in self.variables:
            values=variable.value()
            if type(values)==list:
                for value in values:
                    variable.current_histogram.Fill(value)
            else:
                variable.current_histogram.Fill(values) 

    def deinit_eventfile(self,event_file):
        if self.norm_mode=='none':
            return
        elif self.norm_mode=='1':
            scale=1
        elif self.norm_mode=='xsec':
            scale=event_file.effxsec
    
        for variable in self.variables:
            variable.current_histogram.Scale(scale/variable.current_histogram.GetEntries())

    def deinit(self):
        # Draw everything
        for variable in self.variables:
            name="c1_%s"%variable.__class__.__name__
            c=TCanvas(name,name)
            self.store(c)
#            c.SetLogy(True)
            if self.stack:
                variable.histogram.Draw()
            else:
                variable.histogram.Draw('nostack')
            variable.histogram.GetXaxis().SetTitle(variable.title)

            if variable.histogram.GetHists().GetSize()>1: # Only bother with legend if have more
                                                          # than one event file
                l=c.BuildLegend(.65,.65,.95,.95)
                self.store(l)
                l.Draw()
            c.Update()

            # Print it out
            c.SaveAs("%s.png"%name)

            # Dump some stats, while we are there..
            print variable.title
            for hist in variable.histogram.GetHists():
                print "\t%s\t%f\t%f"%(hist.GetTitle(),hist.GetMean(),hist.GetRMS())

        

