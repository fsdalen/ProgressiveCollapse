#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName     = 'shellSimple'
cpus        = 2			#Number of CPU's
monitor     = 1


run         = 0
blastTime   = 0.05
TNT         = 1.0	#tonns of tnt

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt = SINGLE #SINGLE or FULL

#Post
defScale    = 1.0
printFormat = PNG 	#TIFF, PS, EPS, PNG, SVG
fieldIntervals = 1000
histIntervals = fieldIntervals
animeFrameRate = 5




#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.shell as shell
reload(func)
reload(shell)


modelName   = mdbName

steel = 'DOMEX_S355'
concrete = 'Concrete'
rebarSteel = 'Rebar Steel'

#Set up model with materials
func.perliminary(monitor, modelName, steel, concrete, rebarSteel)

M=mdb.models[modelName]



#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
shell.createSingleBeam(modelName, steel)


#Create setp
oldStep = 'Initial'
stepName = 'blast'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=blastTime)

#Create blast
shell.conWep(modelName, TNT = TNT, blastType=SURFACE_BLAST,
	coordinates = (-10000.0, 0.0, 0.0),
	timeOfBlast =0.0, stepName=stepName)




#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(numIntervals=fieldIntervals)

#IWCONWEP field output
M.FieldOutputRequest(createStepName=stepName, name=
	'IWCONWEP', numIntervals=fieldIntervals, rebar=EXCLUDE, region=
	M.rootAssembly.allInstances['Part-2-1'].sets['face']
	, sectionPoints=DEFAULT, variables=('IWCONWEP', ))

#Delete default history output
del M.historyOutputRequests['H-Output-1']


#Create U history output
regionDef=M.rootAssembly.allInstances['Part-1-1'].sets['midNodes']
M.HistoryOutputRequest(name='displacement', 
    createStepName=stepName, variables=('U1', ), region=regionDef, 
    sectionPoints=DEFAULT, rebar=EXCLUDE, numIntervals=histIntervals)


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

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	#=========== Contour  ============#
	# func.countourPrint(modelName, defScale, printFormat)

	#=========== Animation  ============#
	# func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	#=========== XY  ============#
	shell.xySimpleDef(modelName, printFormat)
	shell.xySimpleIWCONWEP(modelName, printFormat)
	print '   done'


print '###########    END OF SCRIPT    ###########'
