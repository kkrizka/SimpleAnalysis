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
#  onlyaxis: make this only the 'x' or 'y' axis in correlations ('both' by default)
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
        for i1 in range(len(self.variables)):
            var1=self.variables[i1]
            var1.onlyaxis='both' if not hasattr(var1,'onlyaxis') else var1.onlyaxis
            for i2 in range(len(self.variables)):
                if i1==i2: continue
                
                var2=self.variables[i2]
                var2.onlyaxis='both' if not hasattr(var2,'onlyaxis') else var2.onlyaxis
                for category in self.categories:
                    h=self.create_category(category,var1,var2)
                    if h==None: continue
                    
                    # Save to the histograms array
                    key=(i1,i2)
                    if key not in self.histograms:
                        self.histograms[key]={}
                    self.histograms[key][category.name]=h


    def create_category(self,category,var1,var2):
        # Axis settings
        if var1.onlyaxis==var2.onlyaxis and var1.onlyaxis!='both': return None # Skip duplicates

        if var1.onlyaxis not in ['x','both']: return # var1 is y-axis..
        #
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
        h.var1=var1
        h.var2=var2
        h.category=category.name

        return h

    def run_event(self):
        category=self.category.value() if self.category!=None else 'default'
        if category==None: return

        # Get values for all of the variables
        values=[]
        for variable in self.variables:
            value=variable.wvalue()
            if value!=None and type(value)!=list: value=[value]
            values.append(value)

        # Get the length of the value lists. We assume that all variables
        # have the same length.
        nValues=len(values[0])
        nValuesRange=range(nValues)

        # Prepare a list of corresponding categories
        if type(category)!=list:
            vcategory=[category]*nValues
        else:
            vcategory=category
            
        # Fill the histograms
        for key,histogram in self.histograms.items():
            i1,i2=key
            values1=values[i1]
            if values1==None: continue # Do not fill if no value returned
            values2=values[i2]
            if values2==None: continue # Do not fill if no value returned

            for j in nValuesRange:
                val1=values1[j]
                val2=values2[j]
                vcat=vcategory[j]
                if vcat==None: continue
                if vcat in histogram: histogram[vcat].Fill(val1[0],val2[0],val1[1])
                    
    def deinit(self):
        # Draw
        c=TCanvas('c1','c1')
        if self.logz:
            c.SetLogz(True)

        # Turn the histogram list into a dictionary
        histograms=[]
        for key,hists in self.histograms.items():
            for cat,h in hists.items():
                if h.Integral()==0.: continue # Skip empties
                histograms.append(h)

        # Loop and save
        for h in histograms:
            # Normalize histograms, if requested
            if self.norm_mode=='1':
                h.Scale(1./h.Integral())
            
            title1=h.var1.title
            units1=getattr(h.var1,'units',None)
            if units1!=None: title1+=' (%s)'%h.var1.units
            h.SetXTitle(title1)

            title2=h.var2.title
            units2=getattr(h.var2,'units',None)
            if units2!=None: title2+=' (%s)'%h.var2.units
            h.SetYTitle(title2)

            if self.output_type in ['png','eps']: # Draw if saving image
                c.Clear()
                h.Draw('COLZ')

            # Print it out
            outfileName=h.GetName().replace('/','-')
            if self.output_type=='png':
                c.SaveAs("%s.png"%outfileName)
            elif self.output_type=='eps':
                c.SaveAs("%s.eps"%outfileName)
            elif self.output_type=='root':
                f=OutputFactory.getTFile()
                f.cd()
                h.Write()

