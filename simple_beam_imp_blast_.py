#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'simpleBeamImpBlast'
cpus           = 1			#Number of CPU's
monitor        = 1


run            = 0
blastTime      = 0.02
inInc          = 1e-5
minInc         = 1e-12
maxNrInc	   = 500


#Post
defScale       = 1.0
printFormat    = PNG 	#TIFF, PS, EPS, PNG, SVG
animeFrameRate = 5




#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.beam as beam
import lib.singleCol as singleCol
reload(func)
reload(beam)
reload(singleCol)

modelName   = mdbName

steel = 'DOMEX_S355'
concrete = 'Concrete'
rebarSteel = 'Rebar Steel'

#Set up model with materials
func.perliminary(monitor, modelName)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
singleCol.createSingleBeam(modelName)


#Create setp
oldStep = 'Initial'
stepName = 'blast'


M.ImplicitDynamicsStep(initialInc=inInc, minInc=minInc,
	name=stepName, nlgeom=ON, previous=oldStep, timePeriod=blastTime,
	maxNumInc=maxNrInc)

#Create blast
func.blast(modelName, stepName, 
	sourceCo = (-10000.0, 0.0, 0.0),
	refCo = (-50.0, 0.0, 0.0))



#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

#Field damage output
M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS') )

#Delete default history output
del M.historyOutputRequests['H-Output-1']


#History output
regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-base']
M.HistoryOutputRequest(name='load-base', 
    createStepName=stepName, variables=('RF1', ), region=regionDef,)

regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-top']
M.HistoryOutputRequest(name='load-top', 
    createStepName=stepName, variables=('RF1', ), region=regionDef,)

regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-mid']
M.HistoryOutputRequest(name='displacement', 
    createStepName=stepName, variables=('U1', ), region=regionDef,)



#===========================================================#
#===========================================================#
#                   Save and run                            #
#===========================================================#
#===========================================================#
M.rootAssembly.regenerate()
#Save model
mdb.saveAs(pathName = mdbName + '.cae')


#Create job
mdb.Job(model=modelName, name=modelName,
	    numCpus=cpus, numDomains=cpus)

#Run job
if run:
	func.runJob(modelName)
	#Write CPU time to file
	func.readMsgFile(modelName, 'results.txt')



#===================================================#
#===================================================#
#                   Post                            #
#===================================================#
#===================================================#

	print 'Post processing...'

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	#=========== Contour  ============#
	# func.countourPrint(modelName, defScale, printFormat)

	#=========== Animation  ============#
	# func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	#=========== XY  ============#
	singleCol.xySimple(modelName, printFormat)

	print '   done'


print '###########    END OF SCRIPT    ###########'
