#!/bin/env python

import sys
import os.path

from ROOT import *

from SimpleAnalysis import Analysis
from SimpleAnalysis import CommonAnalysis
from SimpleAnalysis import OutputFactory
from SimpleAnalysis import VariableFactory

import optparse
import tempfile
import urlparse
import struct

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
options_parser.add_option("-t", "--test", dest="test", action="store_true",
                          help="Test mode. Set results directory to /tmp and loop over only 10 events. Both can be overriden.", metavar="TEST")
options_parser.add_option("-D", "", dest="define", action="append",
                          help="Define some extra input parameters that can be parsed by analysis scripts.", metavar="KEY[=VALUE]")

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

if options.output==None and options.test:
    options.output=tempfile.mkdtemp()
if options.nevents==None and options.test:
    options.nevents=10

# Build a dictionary of defines
defines={}
if options.define!=None:
    for define in options.define:
        parts=define.split('=')
        if len(parts)==1:
            defines[parts[0]]=True
        else:
            defines[parts[0]]=parts[1]

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

    # Determine if a file is a filelist or just a root file
    o=urlparse.urlparse(inpath)
    isROOT=True
    if o.scheme=='': # Filelists can only be local
        fh=open(inpath,'rb')
        identifier=fh.read(4)
        version=fh.read(4)
        identifier=''.join(struct.unpack('cccc',identifier))
        version=struct.unpack('>i',version)[0]

        if version>=1000000: fh.seek(41)
        else: fh.seek(33)
            
        compression=fh.read(4)
        compression=struct.unpack('>i',compression)[0]
        fh.close()
#        print identifier,version,compression
        if identifier=='root' and compression<1000: # Assume the fVersion is not using any numbers in ASCII range
            isROOT=True
        else:
            isROOT=False

    if isROOT:
        print 'isROOT'
        evset=Analysis.EventFile(inpath,intree)
        analysis.eventfiles.append(evset)
    else:
        fh=open(inpath)
        for inpath in fh:
            inpath=inpath.strip()
            if inpath.startswith('#'): continue
            evset=Analysis.EventFile(inpath,intree)
            analysis.eventfiles.append(evset)

analysis.run()
