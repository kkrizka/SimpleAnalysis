import Analysis
import OutputFactory
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
#  norm_mode: "xsec" - cross-section of event, before any of the cuts are 
#                      applied.
#
# If the attribute "stack" is set to False,  then the "nostack" option is used to
# draw the histogams. It is set to True by default.
#
# If the attribute "logy" is set to True, then the y axis is made log scale.
#
# The attribute "output_type" is the type of the output. It can be set to 'png',
# 'eps' or 'root'.
#
# If a variable returns a list of numbers, all of them are added to a histogram
# invididually. If a value is a touple, then the first entry is taken to be the 
# value to fill the histogram and the second is the weight.
#
# The following member attributes of a variable are used:
#  title: The title to put on the x-axis, without units
#  units: The units to put after the title, in brackets. If not defined, then
#         no units are added.
#  nbins,minval,maxval: The binning to be used for the variable.
#
# The EventFile's can have the following optional attributes:
#  title: The title to put into the legend.
#  linecolor: Corresponds to the color that will be used to draw the histogram line.
#  linestyle: Corresponds to the line style of the histogram
#  fillcolor: Corresponds to the color that will be used to fill the histogram.
#  options: Any drawing options that should be used when drawing this histogram
#  xsec: The cross-section to scale each event by
class VariablePlotterAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.variables=[]
        self.norm_mode='none'
        self.stack=True
        self.logy=False
        self.output_type='png'

    def init(self):
        # Book histograms for all the variables
        for variable in self.variables:
            hs=THStack()
            variable.histogram=hs

    def init_eventfile(self):
        # Prepare the histograms for each of the variables for this event
        # file
        for variable in self.variables:
            # Histogram for this file
            h=TH1F("%s-%s-%s"%(variable,self.eventfile.path,self.eventfile.treeName),
                   self.eventfile.title,
                   variable.nbins,
                   variable.minval,
                   variable.maxval)
            if hasattr(self.eventfile,'linecolor'):
                h.SetLineColor(self.eventfile.linecolor)
            if hasattr(self.eventfile,'linestyle'):
                h.SetLineStyle(self.eventfile.linestyle)
            if hasattr(self.eventfile,'fillcolor'):
                h.SetFillColor(self.eventfile.fillcolor)
            if hasattr(self.eventfile,'options'):
                opt=self.eventfile.options
            else:
                opt='HIST'

            h.Sumw2()
            variable.histogram.Add(h,opt)
            variable.current_histogram=h

    def run_event(self):
        for variable in self.variables:
            values=variable.value()
            if type(values)!=list:
                values=[values]
                
            for value in values:
                if type(value)==tuple:
                    variable.current_histogram.Fill(value[0],value[1])
                else:
                    variable.current_histogram.Fill(value)

    def deinit_eventfile(self):
        if self.norm_mode=='none':
            return
        elif self.norm_mode=='1':
            scale=1
        elif self.norm_mode=='xsec':
            scale=self.eventfile.xsec*self.eventfile.eff

        for variable in self.variables:
            if variable.current_histogram.Integral()>0:
                variable.current_histogram.Scale(scale/variable.current_histogram.Integral())

    def deinit(self):
        # Draw everything
        for variable in self.variables:
            c=TCanvas(variable.name,variable.name)
            self.store(c)

            if self.stack:
                variable.histogram.Draw()
            else:
                variable.histogram.Draw('nostack')

            # Build up the axis title
            title=variable.title
            if hasattr(variable,'units') and variable.units!='':
                title+=' (%s)'%variable.units
            variable.histogram.GetXaxis().SetTitle(title)

            # Add a legend, if necessary
            if variable.histogram.GetHists().GetSize()>1: # Only bother with legend if have more
                                                          # than one event file
                l=c.BuildLegend(.65,.65,.98,.95)
                self.store(l)
                l.Draw()

            # Axis type
            if self.logy:
                # Figure out the best range to all of the events are seen on the log scale
                hist=variable.histogram.GetHistogram()
                binn=hist.GetNbinsX()
                binvals=[]
                for bin in range(binn):
                    binvals.append(None)
                
                for hist in variable.histogram.GetHists():
                    for bin in range(binn):
                        val=hist.GetBinContent(bin+1)
                        if val==0: continue # Only care about bins with something in it

                        if binvals[bin]==None:
                            binvals[bin]=val
                            continue

                        if self.stack:
                            binvals[bin]+=val
                        else:
                            if val<binvals[bin]:
                                binvals[bin]=val

                minval=None
                for bin in range(binn):
                    val=binvals[bin]
                    if val==None: continue
                    
                    if minval==None:
                        minval=val
                    else:
                        if val<minval:
                            minval=val
                        
                if minval!=None:
                    variable.histogram.SetMinimum(minval)

                # Set the log scale
                c.SetLogy(True)
                
            c.Update()

            # Print it out
            outfileName="%s-%s"%(self.name,variable.name)
            outfileName=outfileName.replace('/','-')
            if self.output_type=='png':
                c.SaveAs("%s.png"%outfileName)
            elif self.output_type=='eps':
                c.SaveAs("%s.eps"%outfileName)
            elif self.output_type=='root':
                f=OutputFactory.getTFile()
                f.cd()
                variable.histogram.SetName(variable.name)
                variable.histogram.Write()
                
                

            # Dump some stats, while we are there..
            print variable.title
            for hist in variable.histogram.GetHists():
                print "\t%s\t%f\t%f"%(hist.GetTitle(),hist.GetMean(),hist.GetRMS())
