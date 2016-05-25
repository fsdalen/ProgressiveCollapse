#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'simpleBeamBlast09fluidInertia'
cpus           = 1			#Number of CPU's
monitor        = 1


run            = 1
blastTime      = 0.1	#Takes around 0.03 for the wave to pass the building


#Post
defScale       = 1.0
printFormat    = PNG 	#TIFF, PS, EPS, PNG, SVG
fieldIntervals = 30
histIntervals  = 500
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
singleCol.createSimpleBeamGeom(modelName, steel)


#Create setp
oldStep = 'Initial'
stepName = 'blast'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=blastTime)

#Create blast
func.addIncidentWave(modelName, stepName,
	AmpFile= 'blastAmp.txt',
	sourceCo = (-10000.0, 100.0, 0.0),
	refCo = (-1000.0, 100.0, 0.0))




#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(numIntervals=fieldIntervals)

M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'),
    numIntervals=fieldIntervals)

#Delete default history output
del M.historyOutputRequests['H-Output-1']


#History output
regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-base']
M.HistoryOutputRequest(name='load-base', 
    createStepName=stepName, variables=('RF1', ), region=regionDef, 
    numIntervals=histIntervals)

regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-top']
M.HistoryOutputRequest(name='load-top', 
    createStepName=stepName, variables=('RF1', ), region=regionDef, 
    numIntervals=histIntervals)

regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-mid']
M.HistoryOutputRequest(name='displacement', 
    createStepName=stepName, variables=('U1', ), region=regionDef, 
    numIntervals=histIntervals)



#===========================================================#
#===========================================================#
#                   Save and run                            #
#===========================================================#
#===========================================================#
M.rootAssembly.regenerate()
#Save model
mdb.saveAs(pathName = mdbName + '.cae')


#Create job
precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt = SINGLE #SINGLE or FULL
mdb.Job(model=modelName, name=modelName,
	    numCpus=cpus, numDomains=cpus,
	    explicitPrecision=precision, nodalOutputPrecision=nodalOpt)

#Run job
if run:
	func.runJob(modelName)
	#Write CPU time to file
	func.readStaFile(modelName, 'results.txt')



#===================================================#
#===================================================#
#                   Post                            #
#===================================================#
#===================================================#

	print 'Post processing...'

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	# #=========== Contour  ============#
	# func.countourPrint(modelName, defScale, printFormat)

	# #=========== Animation  ============#
	# func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	#=========== XY  ============#
	singleCol.xySimpleBeam(modelName)

	print '   done'


print '###########    END OF SCRIPT    ###########'
