#!/usr/bin/python

import sys
import os.path

from ROOT import *
from SimpleAnalysis import Analysis
from SimpleAnalysis import VariableFactory
from SimpleAnalysis import CommonAnalysis
from SimpleAnalysis import VariablePlotterAnalysis
from SimpleAnalysis import ScatterPlotterAnalysis
from SimpleAnalysis import TrimAnalysis
from SimpleAnalysis import VariableComparatorAnalysis

import optparse

##
# This is a general script to run the analysis on a set of simulated events.
# The variables and cuts to be run are configured in the configuration file,
# which is a separate file specified as the first arugment to this script.
# The rest of the code loops over all of the events that pass a cut and
# calls a function inside the "analysis" variable, which must be defined 
# as a subclass of the Analysis class inside the configuration file.

# Determine the options
usage = "usage: %prog [options] config-file.py"
options_parser=optparse.OptionParser(usage=usage)

(options, args) = options_parser.parse_args()

# ERROR Checking
if len(args) != 1:
    options_parser.print_help();
    sys.exit(-1)

pyfile=args[0]

if not os.path.exists(pyfile):
    print "Error: Requested configuration does not exist!"
    sys.exit(-1)

# Add the script location to path to it can load it's own modules
pypath=os.path.dirname(os.path.abspath(pyfile))
sys.path.append(pypath)

execfile(pyfile) # Load the config file


# Some commond settings to make the plots look pretty
gROOT.SetStyle("Plain");
gStyle.SetOptStat("");
gStyle.SetPalette(1);

# Autoconfigure some parts of the analysis
analysis.name=pyfile[:-3]
analysis.run()
