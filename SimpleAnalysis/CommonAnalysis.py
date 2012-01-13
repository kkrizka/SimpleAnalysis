import Analysis
import TMCHelper

from math import *

### This file contains a few Variable/Cut classes that are common to many
### analysis chains.

### Cuts ###

## A generic cut that uses any variable and rejects events that have the
## variable value less than minVal.
class VariableCut(Analysis.Cut):
    ## Arguments:
    ## - variable: An Analysis.Variable object that cuts will be run on
    ## - minVal: The minimum value of the variable below which events are 
    ##           rejected.
    ## - invert: Boolean indicating whether the cut should be inverted.
    ##           Inverted cuts reject events with values above minVal.
    ##           (Default: False)
    def __init__(self,variable,minVal,invert=False):
        Analysis.Cut.__init__(self,invert)
        self.variable=variable
        self.minVal=minVal

    ## Cut method
    def cut(self,particles):
        value=self.variable.value()
        if(value<self.minVal):
            return True
        return False

## Makes sure that there is a high Pt particle in the event.
class ParticlePtCut(Analysis.Cut):
    ## Arguments:
    ## - pdgCode: The pdg code of the particle to lok for
    ## - minPt: The minimum value of Pt required for this particle
    ## - needFinal: The results must be final state (Default: True)
    ## - invert: Boolean indicating whether the cut should be inverted.
    ##           (Default: False)
    def __init__(self,pdgCode,minPt,needFinal=True,invert=False):
        Analysis.Cut.__init__(self,invert)
        self.pdgCode=pdgCode
        self.minPt=minPt
        self.needFinal=needFinal

    ## Cut method
    def cut(self,particles):
        for i in range(0,particles.GetEntries()):
            particle=particles.At(i)
            if(particle.GetPdgCode()!=self.pdgCode):
                continue
            if(particle.GetNDaughters()>0 and self.needFinal):
                continue
            if(particle.Pt()>self.minPt):
                return False
        return True


### Variables ###
## Sum of different variables
class Sum(Analysis.Variable):
    def __init__(self,variables):
        titles=[]
        minval=0
        maxval=0
        for variable in variables:
            titles.append(variable.title)
            minval+=variable.minval
            maxval+=variable.maxval
        title=' + '.join(titles)
        Analysis.Variable.__init__(self,title)
        self.nbins=100
        self.minval=minval
        self.maxval=maxval

        self.variables=variables
        
    def value(self):
        value=0
        for variable in self.variables:
            value+=variable.value()
        return value

## missing Et - Sum of momenta of all final state neutrinos
class MissingEt(Analysis.Variable):
    def __init__(self):
        Analysis.Variable.__init__(self,"Missing E_{T} (GeV)")
        self.nbins=100
        self.minval=0
        self.maxval=500

    def calculate(self):
        final_particles=TMCHelper.final_state_particles(self.particles,2,False)
        METx=0
        METy=0
        for particle in final_particles:
            code=particle.GetPdgCode()
            if(abs(code)==12 or abs(code)==14 or abs(code)==16):
                METx+=particle.Px()
                METy+=particle.Py()

        return sqrt(METx*METx+METy*METy)
