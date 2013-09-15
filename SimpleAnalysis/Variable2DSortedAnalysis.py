from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
from SimpleAnalysis import Category

from ROOT import *

from array import array

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
#  suffix: Text to append to the end of the saved histograms as varname_suffix (None by default)
#  prefix: Text to append to the beginning of the saved histograms as prefix_varname (None by default)
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
#  bins: A list specifying the variable binning argument to ROOT histograms. If set,
#        nbins/minval/maxval are ignored.
#

class Variable2DSortedAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.category=None
        self.categories=[]

        self.variables=[]
        self.bigtitle=None
        self.suffix=None
        self.prefix=None
        self.norm_mode='none'        
        self.output_type='png'
        self.logz=False

        self.histograms={}

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
        suffix='' if self.suffix==None else '_%s'%self.suffix
        prefix='' if self.prefix==None else '%s_'%self.prefix

        bigtitle=''
        if self.bigtitle!=None: bigtitle=' and %s'%self.bigtitle

        # Determine the binning method for the two variables
        bins=[]
        if hasattr(var1,'bins'):
            bins+=[len(var1.bins)-1,array('d',var1.bins)]
        else:
            bins+=[var1.nbins,var1.minval,var1.maxval]

        if hasattr(var2,'bins'):
            bins+=[len(var2.bins)-1,array('d',var2.bins)]
        else:
            bins+=[var2.nbins,var2.minval,var2.maxval]

        # Make histogram
        h=TH2F("%s%s_%svs%s%s"%(prefix,category.name,var1.name,var2.name,suffix),
               '%s%s'%(category.title,bigtitle),
               *bins)
        h.name2="%s%s_%svs%s%s"%(prefix,category.name,var2.name,var1.name,suffix)
        h.var1=var1
        h.var2=var2
        h.category=category.name

        # Save to the histograms array
        key=(var1,var2)
        if key not in self.histograms:
            self.histograms[key]={}
        self.histograms[key][category.name]=h

    def run_event(self):
        if self.category!=None:
            category=self.category.value()
        else:
            category='default'
        if category==None: return

        for i1 in range(len(self.variables)-1):
            # Prepare var1
            var1=self.variables[i1]
            values1=var1.wvalue()
            if values1==None: continue # Do not fill if no value returned
            if type(values1)!=list:
                values1=[values1]

            # Prepare a list of corresponding categories
            if type(category)!=list:
                vcategory=[category]*len(values1)
            else:
                vcategory=category

            for i2 in range(i1+1,len(self.variables)):
                var2=self.variables[i2]

                # Prepare var2
                values2=var2.wvalue()
                if values2==None: continue # Do not fill if no value returned
                if type(values2)!=list:
                    values2=[values2]

                # Key for this pair
                key=(var1,var2)

                hists=self.histograms[key]

                # Fill the histograms
                for j in range(len(values1)):
                    val1=values1[j]
                    val2=values2[j]
                    vcat=vcategory[j]
                    if vcat==None or vcat not in hists: continue
                    h=hists[vcat]
                    h.Fill(val1[0],val2[0],val1[1])

    def deinit(self):
        # Draw
        c=TCanvas('c1','c1')
        if self.logz:
            c.SetLogz(True)

        # Turn the histogram list into a dictionary
        histograms=[]
        for key,hists in self.histograms.items():
            for cat,h in hists.items():
                histograms.append(h)

        # Loop and save
        for h in histograms:
            c.Clear()

            # Skip empties
            if h.Integral()==0.: continue
            
            # Normalize histograms, if requested
            if self.norm_mode=='1':
                h.Scale(1./h.Integral())
            
            h.Draw('COLZ')

            title1=h.var1.title
            if hasattr(h.var1,'units') and h.var1.units!=None:
                title1+=' (%s)'%h.var1.units
            h.SetXTitle(title1)

            title2=h.var2.title
            if hasattr(h.var2,'units') and h.var2.units!=None:
                title2+=' (%s)'%h.var2.units
            h.SetYTitle(title2)

            c.Update()

            # Print it out
            outfileName=h.GetName().replace('/','-')
            outfileName2=h.name2.replace('/','-')
            if self.output_type=='png':
                c.SaveAs("%s.png"%outfileName)
                c.SaveAs("%s.png"%outfileName2)
            elif self.output_type=='eps':
                c.SaveAs("%s.eps"%outfileName)
                c.SaveAs("%s.eps"%outfileName2)
            elif self.output_type=='root':
                f=OutputFactory.getTFile()
                f.cd()
                h.Write()
                h2=h.Clone(h.name2)
                h2.Write()

