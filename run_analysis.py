#!/bin/env python

import sys
import os.path

from ROOT import *

from SimpleAnalysis import Analysis
from SimpleAnalysis import CommonAnalysis
from SimpleAnalysis import OutputFactory
from SimpleAnalysis import VariableFactory

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

options_parser.add_option("-n", "--nevents", dest="nevents", type="int",
                          help="Number of events to process per file.", metavar="NEVENTS")
options_parser.add_option("-o", "--output", dest="output",
                          help="Path to the results directory.", metavar="OUTPUT")
options_parser.add_option("-i", "--input", dest="input",action="append",
                          help="A list of event files to loop over.", metavar="OUTPUT")

(options, args) = options_parser.parse_args()

# ERROR Checking
if len(args) != 1:
    options_parser.print_help();
    sys.exit(-1)

pyfile=args[0]

if not os.path.exists(pyfile):
    print "Error: Requested configuration does not exist!"
    sys.exit(-1)

# Some commond settings to make the plots look pretty
gROOT.SetStyle("Plain");
gStyle.SetOptStat("");
gStyle.SetPalette(1);
TH1.StatOverflows(True)

# Set the suffix for the OutputFactory, if required
OutputFactory.setResults(options.output)

# Add the script location to path to it can load it's own modules
pypath=os.path.dirname(os.path.abspath(pyfile))
sys.path.append(pypath)

execfile(pyfile) # Load the config file

# Autoconfigure some parts of the analysis
analysis.name=pyfile[:-3]
analysis.nevents=options.nevents

# Autoconfigure event files passed through the command line
if options.input==None: options.input=[]

for input in options.input:
    input_parts=input.split(':')
    if len(input_parts)<2:
        print 'WARNING: Invalid input \'%s\''%input
        continue
    intree=input_parts.pop()
    inpath=':'.join(input_parts)
    evset=Analysis.EventFile(inpath,intree)
    analysis.eventfiles.append(evset)

analysis.run()
