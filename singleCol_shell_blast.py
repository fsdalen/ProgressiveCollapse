#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName     = 'singleColBlastShell'
cpus        = 1			#Number of CPU's
monitor     = 0

run         = 0

blastTime   = 0.02
TNT         = 10.0	#tonns of tnt


seed        = 150.0
steelMatFile= 'mat_15.inp'

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt = SINGLE #SINGLE or FULL


#Post
defScale    = 1.0
printFormat = PNG 	#TIFF, PS, EPS, PNG, SVG
fieldIntervals = 500
histIntervals = fieldIntervals
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
func.perliminary(monitor, modelName, steelMatFile)

M=mdb.models[modelName]



#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
singleCol.createSimpleShellGeom(modelName, steel, seed)


#Create setp
oldStep = 'Initial'
stepName = 'blast'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=blastTime)

#CONWEP blast
func.addConWep(modelName, TNT = TNT, blastType=SURFACE_BLAST,
	coordinates = (-10000.0, 0.0, 0.0),
	timeOfBlast =0.0, stepName=stepName)

#Incident wave
func.addIncidentWave(modelName, stepName,
	AmpFile = 'blastAmp.txt',
	sourceCo = (-10000.0, 0.0, 0.0),
	refCo = (-1000.0, 0.0, 0.0))
	
# #Pressure load
# singleCol.pressureLoad(modelName, stepName,
# 	ampFile='conwepReflected.txt', surf = 'front')




#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(numIntervals=fieldIntervals)

M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('STATUS',), #'SDEG', 'DMICRT',),
    numIntervals=fieldIntervals)

#IWCONWEP field output
# M.FieldOutputRequest(createStepName=stepName, name=
# 	'IWCONWEP', numIntervals=fieldIntervals, rebar=EXCLUDE, region=
# 	M.rootAssembly.allInstances['Part-2-1'].sets['face']
# 	, sectionPoints=DEFAULT, variables=('IWCONWEP', ))

#Delete default history output
del M.historyOutputRequests['H-Output-1']


#U1 history output
regionDef=M.rootAssembly.allInstances['Part-1-1'].sets['mid-side']
M.HistoryOutputRequest(name='U1-midSide', 
    createStepName=stepName, variables=('U1', ), region=regionDef, 
    numIntervals=histIntervals)
regionDef=M.rootAssembly.allInstances['Part-1-1'].sets['mid-back']
M.HistoryOutputRequest(name='U1-midBack', 
    createStepName=stepName, variables=('U1', ), region=regionDef, 
    numIntervals=histIntervals)
regionDef=M.rootAssembly.allInstances['Part-1-1'].sets['mid-front']
M.HistoryOutputRequest(name='U1-midFront', 
    createStepName=stepName, variables=('U1', ), region=regionDef, 
    numIntervals=histIntervals)

#R1 history output
M.HistoryOutputRequest(createStepName=stepName, name='R1-top', 
	region= M.rootAssembly.allInstances['Part-1-1'].sets['top'],
	variables=('RF1', ), numIntervals=histIntervals)
M.HistoryOutputRequest(createStepName=stepName, name='R1-bot', 
	region= M.rootAssembly.allInstances['Part-1-1'].sets['bot'],
	variables=('RF1', ), numIntervals=histIntervals)




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


	#=========== Contour  ============#
	# func.countourPrint(modelName, defScale, printFormat)

	#=========== Animation  ============#
	# func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	#=========== XY  ============#
	singleCol.xyShell(modelName)
	# singleCol.xySimpleIWCONWEP(modelName, printFormat)
	print '   done'


print '###########    END OF SCRIPT    ###########'
