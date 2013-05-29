from ROOT import *

import VariableFactory
import OutputFactory
import PointerFactory
import Timing

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
                is_weights_list=(type(weights)==list)
                if type(self.cached_value)==list: # Apply weight item-by-item
                    for idx in range(len(self.cached_value)):
                        cached_value=self.cached_value[idx]
                        if type(cached_value)!=tuple: # No weight applied yet
                            if is_weights_list:
                                self.cached_value[idx]=(cached_value,weights[idx])
                            else:
                                self.cached_value[idx]=(cached_value,weights)
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
    branch_accessed=None
    def __init__(self,path,treeName):
        self.path=path
        self.treeName=treeName

        self.eff=None

        self.fh=None
        self.tree=None

        self.eventidx=None
        self.branch_pointers={}
        self.branch_type={}
        
        EventFile.branch_accessed=set()

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

    # Load the corresponding event
    def event(self,idx):
        self.tree.GetEntry(idx)
        self.eventidx=idx
        event=Event(self)
        return event
                            

    # Close the file, and cleanup any extra stuff
    def close(self):
        self.fh.Close()
        print '== Branches Used =='
        branch_accessed=sorted(EventFile.branch_accessed)
        for branch in branch_accessed:
            print branch

    # Setups a pointer to a branch and returns it. If creation failed, return None.
    def branch_pointer(self,branchname):
        if branchname in self.branch_pointers: # Check pointer for this branch
            return (self.branch_pointers[branchname],self.branch_type[branchname])

        # Not cached, so create it
        branch=self.tree.GetBranch(branchname)

        # Set status
        self.enable_branch(branch)
        
        # Create a pointer, is possible
        (pointer,thetype)=self.create_pointer(branchname)
        self.branch_pointers[branchname]=pointer
        self.branch_type[branchname]=thetype
        if pointer!=None:
            self.tree.SetBranchAddress(branchname,pointer)
            if self.eventidx!=None: self.tree.GetEntry(self.eventidx)
        return (pointer,thetype)


    def enable_branch(self,branch):
        branch.SetStatus(1)
        for subbranch in branch.GetListOfBranches():
            self.enable_branch(subbranch)

    def create_pointer(self,branchname):
        branch=self.tree.GetBranch(branchname)

        types=[]
        # Check for composite type
        if self.tree.GetBranch('%s.fUniqueID'%branchname)!=None:
            if self.tree.GetBranch('%s.fP.fUniqueID'%branchname)!=None and self.tree.GetBranch('%s.fE'%branchname)!=None:
                types.append('vector<TLorentzVector>')
            else:
                return (None,None) # This is some weird composite type...
        else: # Determine type by looking at leaves
            leaves=branch.GetListOfLeaves()
            for leaf in leaves:
                types.append(leaf.GetTypeName())

        if len(types)>1: return (None,None) # Dunno how to handle structs yet

        # Determine type by obtaining the value the python way
        pointer=PointerFactory.get(types[0])
        if pointer!=None: # Make sure that this is a supported pointer type
            return (pointer,types[0])            
        return (None,None)


## This is a general class for an event. It is up to the reader classes (unimplemented)
## to define any specific variables. The original event from the ROOT tree is always
## accessible through the 'raw' attribute.
##
## All of the branches of the tree are disabled by default, for performance reasons.
## Accessing them through the corresponding attribute of the Event object (ie: event.pt
## to get branch pt) enables them automatically.
##
## Attributes:
##  raw: The raw entry in the TTree for direct access
##  idx: The index inside the TTree of the currently processed eventp
class Event:
    def __init__(self,eventfile):
        self.idx=None
        self.eventfile=eventfile
        self.raw=eventfile.tree
        self.branch_cache={}

    # Returns a pointer to the requested branch
    def __getattr__(self,attr):
        EventFile.branch_accessed.add(attr)

        pointer,thetype=self.eventfile.branch_pointer(attr)
        if pointer!=None:  # Check pointer for this branch
            return self.pointer_value(pointer,thetype)
        if attr in self.branch_cache: # Check if has already been calculated
            return self.branch_cache[attr]

        if hasattr(self.raw,attr): # If it exists, direct access
            self.branch_cache[attr]=self.raw.__getattr__(attr)
            return self.branch_cache[attr]

        raise AttributeError('%r object has no attribute %r'%(type(self),attr))

    def pointer_value(self,pointer,type):
        if type in ['UInt_t','Int_t']:
            return int(pointer[0])
        elif type in ['Float_t','Double_t']:
            return float(pointer[0])
        elif type in ['Bool_t']:
            return bool(pointer[0])
        elif type==std.string:
            return str(pointer)
        else:
            return pointer


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

        timing=Timing.Timing()

        for eventfile in self.eventfiles:
            eventfile.cutflow=[]
            VariableFactory.setEventFile(eventfile)
            VariableFactory.setEvent(None)
            for cut in self.cuts:
                cut.eventfile=eventfile
                cut.event=None
                eventfile.cutflow.append(0)
            self.eventfile=eventfile

            # Open the file
            eventfile.load_tree()
            if eventfile.tree==None:
                print "ERROR: Tree not found!"
                continue
            if eventfile.tree.GetEntries()==0:
                print 'ERROR: Tree has no entries!'
                continue
            eventfile.tree.SetBranchStatus("*",0)
            
            gROOT.cd()

            # Clear the branch pointers in an event
            Event.branch_pointers={}
            Event.branch_type={}

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

            for evt_idx in range(eventfile.tree.GetEntries()):
                events_processed+=1

                if events_processed>nEvents:
                    events_processed=nEvents
                    break

                self.event=eventfile.event(evt_idx)
                self.event.idx=evt_idx
                VariableFactory.setEvent(self.event)

                print "=============================="
                print " Event: %d                    "%self.event.idx
                print "=============================="
                # Check for cuts..
                docut=False
                for cidx in range(len(self.cuts)):
                    cut=self.cuts[cidx]
                    cut.event=self.event
                    if cut.cut()!=cut.invert:
                        docut=True
                        break
                    eventfile.cutflow[cidx]+=1
                if docut:
                    print "!!!! THIS EVENT HAS BEEN CUT !!!!"
                    continue
                else:
                    events_passed+=1
                print ""

                ## Run the user code
                timing.start()
                self.run_event()
                timing.end()

            eventfile.eff=1.0*events_passed/events_processed
            self.deinit_eventfile()
            # Print out a summary
            print 'Cut Flow:'
            for cidx in range(len(eventfile.cutflow)):
                print '\tPassing cut %s: %d'%(self.cuts[cidx].__class__.__name__,eventfile.cutflow[cidx])
            print "Cut Efficiency: %d/%d = %f"%(events_passed,events_processed,(float(events_passed)/events_processed))

            eventfile.close()
        self.deinit()
        print '== End Statistics =='
        print 'Average Time Per Event: %s'%str(timing.average())
            
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
