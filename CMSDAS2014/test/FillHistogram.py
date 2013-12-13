#!usr/bin/python
import sys, getopt
import ROOT
from ROOT import TFile, TTree, TH1, TH1F, TCanvas, TMath, gROOT
from math import *

sample   = ''
trigger  = ''
applySub = False

opts, args = getopt.getopt(sys.argv[1:],'s:t:a:',['sample=','trigger=','substructure='])

for opt, arg in opts:
  if opt in ('-s','--sample'):
    sample = arg
  elif opt in ('-t','--trigger'):
    trigger = arg
  elif opt in ('-a','--substructure'):
    applySub = arg

inputf  = 'root://eoscms//eos/cms/store/cmst3/group/das2014/EXODijetsLE/dijetTree_'+sample+'.root'

outf = ''
if applySub == True:
  outputf = 'dijetHisto_'+sample+'_'+trigger+'_sub.root'
else:
  outputf = 'dijetHisto_'+sample+'_'+trigger+'.root'

gROOT.Reset()
#---- get the tree ---------------------
inf = TFile.Open(inputf)
events = inf.Get('dijets/events')

#---- create the output file -----------
outf = TFile(outputf,'RECREATE')

#---- get the trigger histogram --------
hTrig = inf.Get('dijets/TriggerPass')

#---- list of variables ----------------
eventVarName = ['ht','mjj','dEtajj','dPhijj','metOvSumEt']
eventVarMin  = [0,0,0,0,0]
eventVarMax  = [3000,5000,5,pi,1]
eventVarBins = [300,500,100,100,100]
jetVarName   = ['jetTau21','jetPt','jetEta','jetPhi','jetMass','jetMassPruned']  
jetVarMin    = [0,0,-5,-pi,0,0]
jetVarMax    = [1,2000,5,pi,1000,1000]
jetVarBins   = [100,200,100,100,200,200]
histEventVar = []
histJetVar = []
#---- create the histograms ------------
k = 0
for i in eventVarName:
  h = TH1F('h_'+i,'h_'+i,eventVarBins[k],eventVarMin[k],eventVarMax[k]) 
  h.Sumw2()
  histEventVar.append(h)
  k += 1

k = 0
for i in jetVarName:
  h = TH1F('h_'+i,'h_'+i,jetVarBins[k],jetVarMin[k],jetVarMax[k]) 
  h.Sumw2()
  histJetVar.append(h)
  k += 1  

#---- read the tree & fill histosgrams -
N = events.GetEntriesFast()
print 'Reading the input file: '+inf.GetName()
print 'Number of events: '+str(N)
d = 0

for i in xrange(N):
  events.GetEntry(i)
  #---- progress of the reading --------
  fraction = 10.*i/(1.*N)
  if TMath.FloorNint(fraction) > d:
    print str(10*TMath.FloorNint(fraction))+'%' 
  d = TMath.FloorNint(fraction)

  cut_trigger      = True 
  cut_mass         = True
  cut_substructure = True
  cut_dEtajj       = events.dEtajj < 1.3
  cut_leptonVeto   = events.jetElf[0]<0.7 and events.jetElf[1]<0.7 and events.jetMuf[0]<0.7 and events.jetMuf[1]<0.7
  cut_eta          = fabs(events.jetEta[0])<2.5 and fabs(events.jetEta[1])<2.5
  cut_pt           = events.jetPt[1]>40

  if trigger == 'signal':
    cut_trigger = events.triggerResult[0] or events.triggerResult[1] or events.triggerResult[2] or events.triggerResult[3]
    cut_mass = events.mjj > 890
  elif trigger == 'ref':
    cut_trigger = events.triggerResult[4]
    cut_mass = events.mjj > 0
  elif trigger == 'refSig':
    cut_trigger = events.triggerResult[4] and (events.triggerResult[0] or events.triggerResult[1] or events.triggerResult[2] or events.triggerResult[3])
    cut_mass = events.mjj > 0

  if applySub == True:
    cut_substructure = (
    events.jetMassPruned[0] > 60 and 
    events.jetMassPruned[0] < 100 and 
    events.jetMassPruned[1] > 60 and 
    events.jetMassPruned[1] < 100 and 
    events.jetTau2[0]/events.jetTau1[0] > 0.5 and 
    events.jetTau2[1]/events.jetTau1[1] > 0.5)

  if (cut_trigger and cut_dEtajj and cut_mass and cut_leptonVeto and cut_eta and cut_pt and cut_substructure):
    #---- set the event variables ----
    eventVar = [events.ht,events.mjj,events.dEtajj,events.dPhijj,events.metSig]
    for k in xrange(len(histEventVar)):
      histEventVar[k].Fill(eventVar[k])
    for j in xrange(2):
      #---- set the jet variables ----
      jetVar = [events.jetTau2[j]/events.jetTau1[j],events.jetPt[j],events.jetEta[j],events.jetPhi[j],events.jetMass[j],events.jetMassPruned[j]]
      for k in xrange(len(histJetVar)):
        histJetVar[k].Fill(jetVar[k])
      
#---- write output file ----------------
print 'Writing output file: '+outf.GetName()
outf.cd()
hTrig.Write()
outf.Write()
outf.Close()
inf.Close() 
  