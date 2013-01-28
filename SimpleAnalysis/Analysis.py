from ROOT import *

import VariableFactory
import OutputFactory

##
# This is a general class for calculating a variable for an event. It can also store
# the aesthetic information that will be used when plotting.
#
# It is also possible to define a variable weight, through the weight attribute. This
# weight is then added to the returned value by formatting it as a tuple. The weight
# is another variable that returns either a single value or a list. In the case of a
# single value, the same weight is set for all of the values returned by a variable. If
# it is a list, then the index of the weight list is matched to the index of the value
# list. It is possible to override this weight by having the variable return a tuple
# itself.
#
# Variable values can be automatically cached, which is useful if they are used 
# several times at different parts of the analysis. Only the last value is cached 
# though.
#
# Each variable is required to have set the following properties:
# - name: The name of the variable. Taken to be the class name by default
# - type: The type of the variable. Taken to be float by default.
#
# The following attributes are optional:
# - weight: A Variable object that returns the weight for the event.
#
# Each calculation has the access to the following attributes
# - event: Entry in the TTree currently being processed
# - eventfile: Information about the event file being processed
class Variable:
    # Arguments:
    # - name: The name that will be used to identify this variable
    #         throughout the execution and outputs
    def __init__(self,name=None,type=float):
        if name==None:
            self.name=self.__class__.__name__
        else:
            self.name=name

        self.type=type
        self.weight=None

        # setup the cache
        self.cached_value=None
        self.dirty_bit=True

        self.event=None
        self.eventfile=None

    # All subclasses need to implement this function. This is what is called for
    # each event and it should return the value that this variable represents.
    # Overriding this function disables caching.
    def value(self):
        if self.dirty_bit:
            self.cached_value=self.calculate()
            self.dirty_bit=False

            # Apply weighting, if necessary
            if self.weight!=None and self.cached_value!=None:
                weights=self.weight.value()
                if type(self.cached_value)==list: # Apply weight item-by-item
                    for idx in range(len(self.cached_value)):
                        if type(self.cached_value[idx])!=tuple: # No weight applied yet
                            if type(weights)==list:
                                self.cached_value[idx]=(self.cached_value[idx],weights[idx])
                            else:
                                self.cached_value[idx]=(self.cached_value[idx],weights)
                else:
                    if type(self.cached_value)!=tuple: # No weight applied yet
                        self.cached_value=(self.cached_value,weights)
            
            
        return self.cached_value;

    # All subclasses that wish to cache their results should implement this
    # instead of value(). It works the same way as value().
    def calculate():
        return 0

##
## This is a general class that can be used to implement cuts on a set of 
## simulated events.
##
## The following are some useful member parameters that are available to perform
## analysis when each of the triggers are called.
##  event - The entry in the TTree currently being processed
##  eventfile - The event file being processed
class Cut:
    # Arguments:
    # - invert: Whether to invert this cut. That is, cut when the cut function 
    #           returns False
    def __init__(self,invert=False):
        self.invert=invert

        self.event=None
        self.eventfile=None
    
    # All subclasses need to implement this function. This is what is called for
    # each event and it should return True if the event is to be cut (ignored) or
    # False if it is to be kept (included in further calculations).
    #
    # The return value of this ignores the value of self.invert.
    #
    # The arguments are the list of particles output by the 
    # Pythia8 plugin to ROOT. The list is a TClonesArray filled
    # with TParticles objects.
    def cut(self):
        return False

## This is a class that describes an event file.
## The required input parameters are:
##  path - The path to the ROOT file holding the TPythia8 data
##  treeName - The name of the tree holding the TPythia8 data
##
## There are also some other parameters required by different derivatives
## of the Analysis class.
##
## Parameters stored by the Analysis class are:
##  eff - efficiency of cuts (available only after running analysis)
##  fh - TFile object, when opened
##  tree - The TTree being used
##  
class EventFile:
    def __init__(self,path,treeName):
        self.path=path
        self.treeName=treeName

        self.eff=None

        self.fh=None
        self.tree=None

    # Load the tree from the file and store it into the tree member
    # attribute. Set it to None if the tree is not found.
    #
    # Return: True if sucessful, false otherwise.
    def load_tree(self):
        self.fh=TFile.Open(self.path)
        if self.fh.FindKey(self.treeName)==None:
            return False
        self.tree=self.fh.Get(self.treeName)
        return True

    # Close the file, and cleanup any extra stuff
    def close(self):
        self.fh.Close()


## This is a general class for an event. It is up to the reader classes (unimplemented)
## to define any specific variables. The original event from the ROOT tree is always
## accessible through the 'raw' attribute.
## Attributes:
##  raw: The raw entry in the TTree for direct access
##  idx: The index inside the TTree of the currently processed eventp
class Event:
    def __init__(self,raw):
        self.idx=None
        self.raw=raw

## This is just a general class for doing analysis. It has the following
## functionality:
## - Loops over events inside different event files
## - Calls a function
##   - Before anything is run (init)
##   - When a new event file is opened (init_eventfile)
##   - When an event is processed (run_event)
##   - After an event file is closed (deinit_eventfile)
##   - After everything is completed (deinit)
##
## Everything is run when the run() function is called.
##
## It is also possible to add "cuts", using the Cut classes. When these cuts are
## added, then only events that pass them are processed by the event function.
##
## The following are some useful member parameters that are available to perform
## analysis when each of the triggers are called.
##  event - The entry in the TTree currently being processed
##  eventfile - The event file being processed
##
## Internal parameters that configure this class are:
##  nevents - Causes the analysis to process only the first nevents events from
##            each event file. Set to None to go over all of them. (None by 
##            default)
##  eventfiles - A list of EventFile objects that represent the event files
##               to be looped over.
##  cuts - A list of Cut objects that represent the cuts that will be
##         applied
class Analysis:
    def __init__(self):
        self.nevents=None
        self.eventfiles=[]
        self.cuts=[]

        self.store_list=[]

        self.event=None
        self.eventfile=None

    # Called before stuff is run
    def init(self):
        pass

    # Called before an event file is looped over
    def init_eventfile(self):
        pass

    # Called for each event that passes the cuts
    def run_event(self):
        pass
    
    # Called after an event file is completly looped over
    # The eventfile instance now contains the effective cross-section.
    def deinit_eventfile(self):
        pass

    # Called after stuff is done runnning
    def deinit(self):
        pass

    # This takes care of running everything. After you setup the
    # configuration of your analysis, run this!
    def run(self):
        OutputFactory.setOutputName(self.name)
        self.init()

        for eventfile in self.eventfiles:
            VariableFactory.setEventFile(eventfile)
            VariableFactory.setEvent(None)
            for cut in self.cuts:
                cut.eventfile=eventfile
                cut.event=None
            self.eventfile=eventfile

            # Open the file
            eventfile.load_tree()
            if eventfile.tree==None:
                print "ERROR: Tree not found!"
                continue
            
            gROOT.cd()

            self.init_eventfile()

            print "********************************************************************************"
            print "* Event File: %s   Event Tree: %s       "%(eventfile.path,eventfile.treeName)
            print "* Number of Events: %d                  "%eventfile.tree.GetEntries()
            print "********************************************************************************"

            # Loop over every event
            events_passed=0
            events_processed=0
            
            nEvents=0
            if(self.nevents!=None):
                nEvents=self.nevents
            else:
                nEvents=eventfile.tree.GetEntries()

            for event in eventfile.tree:
                events_processed+=1

                if events_processed>nEvents:
                    events_processed=nEvents
                    break
                
                self.event=Event(event)
                self.event.idx=(events_processed-1)
                VariableFactory.setEvent(self.event)

                print "=============================="
                print " Event: %d                    "%self.event.idx
                print "=============================="
                # Check for cuts..
                docut=False
                for cut in self.cuts:
                    cut.event=self.event
                    if cut.cut()!=cut.invert:
                        docut=True
                        break
                if docut:
                    print "!!!! THIS EVENT HAS BEEN CUT !!!!"
                    continue
                else:
                    events_passed+=1
                print ""

                self.run_event()

            eventfile.eff=1.0*events_passed/events_processed
            self.deinit_eventfile()
            # Print out a summary
            print "Cut Efficiency: %d/%d = %f"%(events_passed,events_processed,(float(events_passed)/events_processed))

            eventfile.close()
        self.deinit()

    # Helps to store stuff during the run of the analysis, so the things are
    # not being deleted.
    def store(self,var):
        self.store_list.append(var)

## This is just a general class for running a script over many ROOT files. It has the following
## functionality:
## - Calls a function
##   - Before anything is run (init)
##   - Once for each event file (run_eventfile)
##   - After everything is completed (deinit)
##
## Everything is run when the run() function is called.
##
## The following are some useful member parameters that are available to perform
## analysis when each of the triggers are called.
##  eventfile - The event file being processed
##
## Internal parameters that configure this class are:
##  nevents - Causes the analysis to process only the first nevents events from
##            each event file. Set to None to go over all of them. (None by 
##            default)
##  eventfiles - A list of EventFile objects that represent the event files
##               to be looped over.
class Script:
    def __init__(self):
        self.nevents=None
        self.eventfiles=[]
        self.cuts=[]

        self.store_list=[]

        self.event=None
        self.eventfile=None

    # Called before stuff is run
    def init(self):
        pass

    # Called for each event file
    def run_eventfile(self):
        pass

    # Called after stuff is done runnning
    def deinit(self):
        pass

    # This takes care of running everything. After you setup the
    # configuration of your analysis, run this!
    def run(self):
        OutputFactory.setOutputName(self.name)
        self.init()

        for eventfile in self.eventfiles:
            VariableFactory.setEventFile(eventfile)
            VariableFactory.setEvent(None)
            self.eventfile=eventfile

            # Open the file
            eventfile.load_tree()
            if eventfile.tree==None:
                print "ERROR: Tree not found!"
                continue
            
            gROOT.cd()

            print "********************************************************************************"
            print "* Event File: %s   Event Tree: %s       "%(eventfile.path,eventfile.treeName)
            print "* Number of Events: %d                  "%eventfile.tree.GetEntries()
            print "********************************************************************************"
            self.run_eventfile()
                        
            eventfile.close()

        self.deinit()

    # Helps to store stuff during the run of the analysis, so the things are
    # not being deleted.
    def store(self,var):
        self.store_list.append(var)
