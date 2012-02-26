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
# The following member attributes of each variable are used to configure its
# appearance:
#  color: The color use to draw it
#  title: The title to put in the legend for it
#  units: The units to put on the x-axis of the plot. Only the first variable's
#         value will be used
#
# Other member attributes are:
#  histograms: List of histograms for each of the variable. The list has the same
#              ordering as the variables list. This is filled in the init phase
#              of the analysis.
class VariableComparatorAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.variables=[]

        self.histograms=[]

    def init(self):
        # Book histograms for all the variables
        for variable in self.variables:
            h=TH1F("%s_%d"%(variable.name,id(variable)),
                   variable.title,
                   variable.nbins,
                   variable.minval,
                   variable.maxval)
            h.SetLineColor(variable.color)

            self.histograms.append(h)

    def event(self,particles):
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
            hist.Scale(1/hist.Integral())
            hs.Add(hist)

        # Draw
        c=TCanvas('c1','c1')

        hs.Draw('nostack')
        hs.GetXaxis().SetTitle('(%s)'%self.variables[0].units)

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
