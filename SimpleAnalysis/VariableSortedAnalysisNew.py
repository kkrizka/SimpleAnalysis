from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
from SimpleAnalysis import Category

from ROOT import *

# This is a general class to compare variables for a set of simulated events,
# but split into different categories based on some selection. No distinction
# is made between the different event files. They are all  stored in the same
# histogram.
#
# The category that should be used should be returned by the category attribute,
# which is a variable. Setting this value to None makes the code to ignore the
# entry. The drawing attributes of a category should be configured through the
# Category object, added to the categories list attribute. This object has the
# requires the following optional attributes:
#  linecolor: Color to use to draw the line
#  linestyle: Style used to draw the line
#  fillcolor: Color to use to fill the histogram
#
# If a variable to be plotted returns a list of numbers, all of them are added to
# a histogram invididually. The category variable can return a list of the same
# size to sort each entry into a different category.
#
# For Variable objects, the following attributes should be set to configure the
# x-axis:
#  title: The title to put on the x-axis
#  units: The units to put on the x-axis of the plot. None means no units
#  nbins: Number of bins in histogram
#  minval: Minimum value in histogram
#  maxval: Maximum value in histogram
#
class VariableSortedAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.category=None
        self.categories=[]

        self.variables=[]

    def init(self):
        # Create a default category, if none exist
        if len(self.categories)==0:
            category=Category.Category('default','Default')
            self.categories.append(category)    
            
        # Book histograms for all the variables
        for variable in self.variables:
            variable.categories={}
            for category in self.categories:
                self.book_category(variable,category)

    def book_category(self,variable,category):
        h=TH1F("%s_%s"%(variable.name,category.name),
               category.title,
               variable.nbins,
               variable.minval,
               variable.maxval)
        if hasattr(category,'linecolor'):
            h.SetLineColor(category.linecolor)
        if hasattr(category,'linestyle'):
            h.SetLineStyle(category.linestyle)
        if hasattr(category,'fillcolor'):
            h.SetFillColor(category.fillcolor)
        if hasattr(category,'options'):
            h.SetOption(category.options)
        else:
            h.SetOption('HIST')

        # Set x-axis title
        title=variable.title
        if hasattr(variable,'units') and variable.units!=None:
            title+=' (%s)'%variable.units
        h.SetXTitle(title)


        variable.categories[category.name]=h

    def run_event(self):
        if self.category!=None:
            category=self.category.value()
        else:
            category='default'
        if category==None: return

        for i in range(len(self.variables)):
            variable=self.variables[i]

            # Get the value to fill the histogram with
            values=variable.wvalue()

            if values==None: continue # Do not fill if no value returned
            if type(values)!=list:
                values=[values]

            # Prepare a list of corresponding categories
            if type(category)!=list:
                vcategory=[category]*len(values)
            else:
                vcategory=category

            if len(vcategory)!=len(values):
                print 'ERROR: variable count != category count'
                continue

            # Fill the histograms
            for j in range(len(values)):
                value=values[j]
                vcat=vcategory[j]
                if vcat==None or vcat not in variable.categories: continue
                h=variable.categories[vcat]
                if type(value)==tuple:
                    h.Fill(value[0],value[1])
                else:
                    h.Fill(value)

    def deinit(self):
        # Get list of histograms to save
        hists={}

        for variable in self.variables:
            # Make a list of histograms
            for category,h in variable.categories.items():
                if h.Integral()==0: continue # ignore empty histograms
                h.Sumw2()
                if variable.name in hists:
                    hists[variable.name].append(h)
                else:
                    hists[variable.name]=[h]

        if len(hists.items())>0:
            f=OutputFactory.getTFile()
            f.cd()
            for dirname,hs in hists.items():
                f.mkdir(dirname)
                f.cd(dirname)
                for h in hs:
                    h.Write()
                f.cd()


