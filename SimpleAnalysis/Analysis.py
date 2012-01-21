from ROOT import *

import VariableFactory

##
# This is a general class for calculating a variable for an
# event. It also stores the aesthetic information that will
# be used when plotting.
#
# Variable values can be automatically cached, which is useful
# if they are used several times at different parts of the
# analysis. Only the last value is cached though.
#
# Each calculation has the access to the following attributes
# - eventID: The ID of the event inside the tree that it is stored in
# - particle: The list containing all of the particles in the event
class Variable:
    # Arguments:
    # - title: The title that will be shown on the x-axis
    def __init__(self,title):
        self.eventID=None
        self.particles=None
        self.title=title
        self.name=self.__class__.__name__

        # setup the cache
        self.cached_eventID=None
        self.cached_value=0

    # All subclasses need to implement this function. This is
    # what is called for each event and it should return the
    # value that this variable represents. Overriding this
    # function disables caching.
    def value(self):
        if(self.eventID!=self.cached_eventID):
            self.cached_eventID=self.eventID
            self.cached_value=self.calculate()
            
        return self.cached_value;

    # All subclasses that wish to cache their results should
    # implement this instead of value(). It works the same way
    # as value().
    def calculate():
        return 0

##
# This is a general class that can be used to implement cuts
# on a set of simulated events.
class Cut:
    # Arguments:
    # - invert: Whether to invert this cut. That is, cut when
    #           the cut function returns False
    def __init__(self,invert=False):
        self.invert=invert
    
    # All subclasses need to implement this function. This is
    # what is called for each event and it should return True
    # if the event is to be cut (ignored) or False if it is 
    # to be kept (included in further calculations).
    #
    # The return value of this ignores the value of self.invert.
    #
    # The arguments are the list of particles output by the 
    # Pythia8 plugin to ROOT. The list is a TClonesArray filled
    # with TParticles objects.
    # 
    # Arguments:
    # - particles: TClonesArray of TParticle objects
    def cut(self,particles):
        return False

## This is a class that describes an event file.
## The required input parameters are:
##  path - The path to the ROOT file holding the TPythia8 data
##  treeName - The name of the tree holding the TPythia8 data
##  xsec - The cross-section in pb for the process in the event file
##  title - The title of the process, used to display it in different parts
##
## There are also some other parameters required by different derivatives
## of the Analysis class.
##
## Parameters stored by the Analysis class are:
##  effxsec - xsec * efficiency of cuts (available only after running analysis)
##  
class EventFile:
    def __init__(self,path,treeName,xsec,title):
        self.path=path
        self.treeName=treeName
        self.xsec=xsec
        self.title=title
        self.effxsec=xsec


## This is just a general class for doing analysis. It has the following
## functionality:
## - Loops over events inside different event files
## - Calls a function
##   - Before anything is run (init)
##   - When a new event file is opened (init_eventfile)
##   - When an event is processed (event)
##   - After an event file is closed (deinit_eventfile)
##   - After everything is completed (deinit)
##
## Everything is run when the run() function is called.
##
## It is also possible to add "cuts", using the Cut classes. When these cuts
## are added, then only events that pass them are processed by the event 
## function.
##
## Internal parameters that configure this class are:
##  test - Causes the analysis to process only the first 10 files from each event file.
##         (False by default)
##  eventfiles - A list of EventFile objects that represent the event files
##               to be looped over.
##  cuts - A list of Cut objects that represent the cuts that will be
##         applied
class Analysis:
    def __init__(self):
        self.test=False
        self.eventfiles=[]
        self.cuts=[]

        self.store_list=[]

    # Called before stuff is run
    def init(self):
        pass

    # Called before an event file is looped over
    def init_eventfile(self,event_file):
        pass

    # Called for each event that passes the cuts
    def event(self,particles):
        pass
    
    # Called after an event file is completly looped over
    # The event_file instance now contains the effective cross-section.
    def deinit_eventfile(self,event_file):
        pass

    # Called after stuff is done runnning
    def deinit(self):
        pass

    # This takes care of running everything. After you setup the
    # configuration of your analysis, run this!
    def run(self):
        self.init()

        self.particles=TClonesArray("TParticle",1000)
        VariableFactory.setParticles(self.particles)

        for event_file in self.eventfiles:
            # Open the file
            f=TFile(event_file.path)
            if f.FindKey(event_file.treeName)==None:
                print "ERROR: Tree not found!"
                continue
            t=f.Get(event_file.treeName)
            

            t.SetBranchAddress("particle",self.particles)

            gROOT.cd()

            self.init_eventfile(event_file)

            print "********************************************************************************"
            print "* Event File: %s                        "%event_file.path
            print "* Cross-section: %f pb                  "%event_file.xsec
            print "* Number of Events: %d                  "%t.GetEntries()
            print "********************************************************************************"

            # Loop over every event
            events_passed=0
            events_processed=0

            nEvents=0
            if(self.test):
                nEvents=10
            else:
                nEvents=t.GetEntries()
            for i in range(0,nEvents):
                VariableFactory.setEventID(i)
                t.GetEntry(i)
                events_processed+=1
                
                print "=============================="
                print " Event: %d                    "%i
                print "=============================="
                # Check for cuts..
                docut=False
                for cut in self.cuts:
                    if cut.cut(self.particles)!=cut.invert:
                        docut=True
                        break
                if docut:
                    print "!!!! THIS EVENT HAS BEEN CUT !!!!"
                    continue
                else:
                    events_passed+=1
                print " # Particles: %d"%self.particles.GetEntries()
                print ""

                self.event(self.particles)

            event_file.effxsec=1.0*event_file.xsec*events_passed/events_processed
            self.deinit_eventfile(event_file)
            # Print out a summary
            print "Cut Efficiency: %f"%(float(events_passed)/events_processed)
            print "Effective Cross-section (xsec*cut_efficiency): %f"%(event_file.effxsec)

            f.Close()
        self.deinit()

    # Helps to store stuff during the run of the analysis, so the things are
    # not being deleted.
    def store(self,var):
        self.store_list.append(var)
