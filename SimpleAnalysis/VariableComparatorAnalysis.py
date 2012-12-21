import Analysis
from ROOT import *
import inspect

# This is a general class to compare variables from a set of simulated events.
# It loops over all of the events that pass a cut and makes a histogram of
# all defined variables. The different histograms are drawn on the same plot
# and are scaled to have an area of 1.
#
# No distinction is made between the different event files. They are all
# stored in the same histogram.
#
# If a variable returns a list of numbers, all of them are added to a histogram
# invididually.  If a value is a touple, then the first entry is taken to be the
# value to fill the histogram and the second is the weight.
#
# The following attributes can be set to control the logic of the analysis:
#  title: The title to put on the x-axis
#  units: The units to put on the x-axis of the plot. None means no units
#  logy: Whether to log the y axis
#  nbins: Number of bins in histogram
#  minval: Minimum value in histogram
#  maxval: Maximum value in histogram
#
# The following member attributes of each variable are used to configure its
# appearance:
#  color: The color use to draw it
#  line: corresponds to the line style of the histogram
#  title: The title to put in the legend for it
#
# Other member attributes are:
#  histograms: List of histograms for each of the variable. The list has the same
#              ordering as the variables list. This is filled in the init phase
#              of the analysis.
class VariableComparatorAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.variables=[]
        self.title=''
        self.units=None
        self.logy=False

        self.nbins=100
        self.minval=0
        self.maxval=100

        self.histograms=[]

    def init(self):
        # Book histograms for all the variables
        for variable in self.variables:
            h=TH1F("%s_%d"%(variable.name,id(variable)),
                   variable.title,
                   self.nbins,
                   self.minval,
                   self.maxval)
            if hasattr(variable,'color'):
                h.SetLineColor(variable.color)
            if hasattr(variable,'line'):
                h.SetLineStyle(variable.line)

            self.histograms.append(h)

    def run_event(self):
        for i in range(0,len(self.variables)):
            variable=self.variables[i]
            values=variable.value()
            if type(values)!=list:
                values=[values]

            h=self.histograms[i]
            for value in values:
                if type(value)==tuple:
                    h.Fill(value[0],value[1])
                else:
                    h.Fill(value)

    def deinit(self):
        # Prepare stack
        hs=THStack()

        for hist in self.histograms:
            hs.Add(hist)

        # Draw
        c=TCanvas('c1','c1')
        if self.logy:
            c.SetLogy(True)

        hs.Draw('nostack')

        title=self.title
        if self.units!=None:
            title+=' (%s)'%self.units
        hs.GetXaxis().SetTitle(title)

        l=c.BuildLegend(.65,.65,.98,.95)
        l.Draw()
        c.Update()

        # Print it out
        outfileName="%s"%(self.name)
        outfileName=outfileName.replace('/','-')
        c.SaveAs("%s.png"%outfileName)

        # Dump some stats, while we are there..
        print "Statistics:"
        for hist in self.histograms:
            print "\t%s\t%f\t%f"%(hist.GetTitle(),hist.GetMean(),hist.GetRMS())
