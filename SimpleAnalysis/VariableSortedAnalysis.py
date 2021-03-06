from SimpleAnalysis import Analysis
from SimpleAnalysis import OutputFactory
from SimpleAnalysis import Category

from ROOT import *

from array import array

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
# size to sort each entry into a different category. To add weighting to a variable,
# just add it to the variables list as a tuple (variable,weight).
#
# The following attributes can be set to control the logic of the analysis:
#  bigtitle: The title to put on the overall graph
#  suffix: Text to append to the end of the saved histograms as varname_suffix (None by default)
#  prefix: Text to append to the beginning of the saved histograms as prefix_varname (None by default)
#  output_type: Type of output ('png', 'eps' or 'root')
#  norm_mode: How to normalize individual histograms ('none' or '1')
#  logy: Whether to log the y axis
#  sort_graphs: Sort graphs by integral before adding them to THStack (default: False)
#  stack: Whether to stack the histograms (True by default)
#
# For Variable objects, the following attributes should be set to configure the
# x-axis:
#  title: The title to put on the x-axis
#  units: The units to put on the x-axis of the plot. None means no units
#  nbins: Number of bins in histogram
#  bins: A list specifying the variable binning argument to ROOT histograms. If set,
#        nbins/minval/maxval are ignored.
#  minval: Minimum value in histogram
#  maxval: Maximum value in histogram
#
class VariableSortedAnalysis(Analysis.Analysis):
    def __init__(self):
        Analysis.Analysis.__init__(self)

        self.category=None
        self.categories=[]

        self.variables=[]
        self.bigtitle=''
        self.suffix=None
        self.prefix=None
        self.norm_mode='none'        
        self.output_type='png'
        self.sort_graphs=False
        self.logy=False
        self.stack=True

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
        suffix='' if self.suffix==None else '_%s'%self.suffix
        prefix='' if self.prefix==None else '%s_'%self.prefix

        # Determine the binning method for the two variables
        bins=[]
        if hasattr(variable,'bins'):
            bins+=[len(variable.bins)-1,array('d',variable.bins)]
        else:
            bins+=[variable.nbins,variable.minval,variable.maxval]


        h=TH1F("%s_%s_%s_%s"%(prefix,variable.name,category.name,suffix),
               category.title,
               *bins)
        if hasattr(category,'linecolor'):
            h.SetLineColor(category.linecolor)
        if hasattr(category,'linestyle'):
            h.SetLineStyle(category.linestyle)
        if hasattr(category,'fillcolor'):
            h.SetFillColor(category.fillcolor)
        if hasattr(category,'options'):
            h.opt=category.options
        else:
            h.opt='HIST'

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
                if vcat==None or vcat not in variable.categories: # This is an uncategorized thing
                    vcat=None
                    if vcat not in variable.categories: continue # We do not have a "default" category
                h=variable.categories[vcat]
                h.Fill(value[0],value[1])

    def deinit(self):
        suffix='' if self.suffix==None else '_%s'%self.suffix
        prefix='' if self.prefix==None else '%s_'%self.prefix

        if self.output_type=='root':
            f=OutputFactory.getTFile()
            f.cd()

        # Draw
        c=TCanvas()
        if self.logy:
            c.SetLogy(True)

        for variable in self.variables:
            c.Clear()

            ## Create a stacked histogram
            variable.hist=THStack(prefix+variable.name+suffix,self.bigtitle)

            # Make a list of histograms
            hists=[]
            for category in self.categories:
                h=variable.categories[category.name]
                if h.Integral()==0: continue # ignore empty histograms
                hists.append(h)
            if len(hists)==0: continue
            if self.sort_graphs: hists=sorted(hists,key=lambda h: h.Integral())

            # Add histograms
            for h in hists:
                if self.norm_mode=='1': h.Scale(1./h.Integral())
                h.Sumw2()
                variable.hist.Add(h,h.opt)

            ## Draw it
            opts=''
            if not self.stack:
                opts+='nostack'
            variable.hist.Draw(opts)
            if variable.hist.GetXaxis().GetLabels()!=None: variable.hist.GetXaxis().LabelsOption('v')

            title=variable.title
            if hasattr(variable,'units') and variable.units!=None:
                title+=' (%s)'%variable.units
            variable.hist.GetXaxis().SetTitle(title)

            if len(hists)>1:
                l=c.BuildLegend(.65,.98-len(hists)*0.04,.98,.98)
                l.Draw()
            c.Update()

            # Print it out
            outfileName="%s-%s"%(self.name,variable.hist.GetName())
            outfileName=outfileName.replace('/','-')
            if self.output_type=='png':
                c.SaveAs("%s.png"%outfileName)
            elif self.output_type=='eps':
                c.SaveAs("%s.eps"%outfileName)
            elif self.output_type=='root':
                variable.hist.Write()

