import Analysis
from ROOT import *
import inspect

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
# invididually. If a value is a touple, then the first entry is taken to be the value to
# fill the histogram and the second is the weight.
#
# The following member attributes of a variable are used:
#  title: The title to put on the x-axis, without units
#  units: The units to put after the title, in brackets. If not defined, then
#         no units are added.
#  nbins,minval,maxval: The binning to be used for the variable.
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
            h=TH1F("%s-%s-%s"%(variable,event_file.path,event_file.treeName),
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
            if type(values)!=list:
                values=[values]
                
            for value in values:
                if type(value)==tuple:
                    variable.current_histogram.Fill(value[0],value[1])
                else:
                    variable.current_histogram.Fill(value)

    def deinit_eventfile(self,event_file):
        if self.norm_mode=='none':
            return
        elif self.norm_mode=='1':
            scale=1
        elif self.norm_mode=='xsec':
            scale=event_file.effxsec

        for variable in self.variables:
            if variable.current_histogram.GetEntries()>0:
                variable.current_histogram.Scale(scale/variable.current_histogram.Integral())

    def deinit(self):
        # Draw everything
        for variable in self.variables:
            c=TCanvas(variable.name,variable.name)
            self.store(c)
#            c.SetLogy(True)
            if self.stack:
                variable.histogram.Draw()
            else:
                variable.histogram.Draw('nostack')

            # Build up the axis title
            title=variable.title
            if hasattr(variable,'units'):
                title+=' (%s)'%variable.units
            variable.histogram.GetXaxis().SetTitle(title)

            # Add a legend, if necessary
            if variable.histogram.GetHists().GetSize()>1: # Only bother with legend if have more
                                                          # than one event file
                l=c.BuildLegend(.65,.65,.98,.95)
                self.store(l)
                l.Draw()
            c.Update()

            # Print it out
            outfileName="%s-%s"%(self.name,variable.name)
            outfileName=outfileName.replace('/','-')
            c.SaveAs("%s.png"%outfileName)

            # Dump some stats, while we are there..
            print variable.title
            for hist in variable.histogram.GetHists():
                print "\t%s\t%f\t%f"%(hist.GetTitle(),hist.GetMean(),hist.GetRMS())
