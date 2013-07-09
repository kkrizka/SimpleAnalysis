from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
from SimpleAnalysis import Category

from ROOT import *

# This is a general class that crates 2D histograms, one per category that is
# based on some selection. No distinction is made between the different event
# files. They are all stored in the same histogram.
#
# The category that should be used should be returned by the category attribute,
# which is a variable. Setting this value to None makes the code to ignore the
# entry. The drawing attributes of a category should be configured through the
# Category object, added to the categories list attribute. This object has the
# following attributes:
#  name: The name used to match to values returned by the category variable
#  title: Title used inside the legend
#
# The x/y variables are all possible combinations of the variables stored inside
# the variables list.
#
# If a variable to be plotted returns a list of numbers, all of them are added to
# a histogram invididually. The category variable can return a list of the same
# size to sort each entry into a different category.
#
# The following attributes can be set to control the logic of the analysis:
#  bigtitle: The title to put on each graph (default: None)
#  suffix: A suffix to append at the end of the name (default: None)
#  output_type: Type of output ('png', 'eps' or 'root')
#  norm_mode: How to normalize individual histograms ('none' or '1')
#  logz: Whether to log the z axis
#
# For Variable objects, the following attributes should be set to configure the
# axes:
#  title: The title to put on the x-axis
#  units: The units to put on the x-axis of the plot. None means no units
#  nbins: Number of bins in histogram
#  minval: Minimum value in histogram
#  maxval: Maximum value in histogram
#

class Variable2DSortedAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.category=None
        self.categories=[]

        self.variables=[]
        self.bigtitle=None
        self.suffix=None
        self.norm_mode='none'        
        self.output_type='png'
        self.logz=False

        self.histograms=[]

    def init(self):
        # Create a default category, if none exist
        if len(self.categories)==0:
            category=Category.Category('default','Default')
            self.categories.append(category)    

        # Book histograms for all the variables
        for i1 in range(len(self.variables)-1):
            var1=self.variables[i1]
            for i2 in range(i1+1,len(self.variables)):
                var2=self.variables[i2]
                for category in self.categories:
                    self.book_category(category,var1,var2)

    def book_category(self,category,var1,var2):
        suffix=''
        if self.suffix!=None: suffix='_%s'%self.suffix

        bigtitle=''
        if self.bigtitle!=None: bigtitle=' and %s'%self.bigtitle

        h=TH2F("%s_%svs%s%s"%(category.name,var1.name,var2.name,suffix),
               '%s%s'%(category.title,bigtitle),
               var1.nbins,
               var1.minval,
               var1.maxval,
               var2.nbins,
               var2.minval,
               var2.maxval)
        h.var1=var1
        h.var2=var2
        h.category=category.name

        self.histograms.append(h)

    def run_event(self):
        if self.category!=None:
            category=self.category.value()
        else:
            category='default'
        if category==None: return

        for h in self.histograms:
            # Get the value to fill the histogram with
            values1=h.var1.wvalue()
            if values1==None: continue # Do not fill if no value returned
            if type(values1)!=list:
                values1=[values1]

            values2=h.var2.wvalue()
            if values2==None: continue # Do not fill if no value returned
            if type(values2)!=list:
                values2=[values2]

            # Prepare a list of corresponding categories
            if type(category)!=list:
                vcategory=[category]*len(values1)
            else:
                vcategory=category

            # Fill the histograms
            for j in range(len(values1)):
                val1=values1[j]
                val2=values2[j]
                vcat=vcategory[j]
                if vcat==None or vcat!=h.category: continue
                if type(val1)==tuple:
                    h.Fill(val1[0],val2[0],val1[1])
                else:
                    h.Fill(val1,val2)

    def deinit(self):
        # Draw
        c=TCanvas('c1','c1')
        if self.logz:
            c.SetLogz(True)

        for h in self.histograms:
            c.Clear()

            # Normalize histograms, if requested
            if self.norm_mode=='1':
                if h.Integral()!=0: h.Scale(1./h.Integral())
            
            h.Draw('COLZ')

            title1=h.var1.title
            if hasattr(h.var1,'units') and h.var1.units!=None:
                title1+=' (%s)'%h.var1.units
            h.GetXaxis().SetTitle(title1)

            title2=h.var2.title
            if hasattr(h.var2,'units') and h.var2.units!=None:
                title2+=' (%s)'%h.var2.units
            h.GetYaxis().SetTitle(title2)

            c.Update()

            # Print it out
            outfileName="%s"%(h.GetName())
            outfileName=outfileName.replace('/','-')
            if self.output_type=='png':
                c.SaveAs("%s.png"%outfileName)
            elif self.output_type=='eps':
                c.SaveAs("%s.eps"%outfileName)
            elif self.output_type=='root':
                f=OutputFactory.getTFile()
                f.cd()
                h.Write()

