#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName     = 'simpleShellBlast'
cpus        = 1			#Number of CPU's
monitor     = 1


run         = 1
blastTime   = 0.1
TNT         = 10.0	#tonns of tnt




#Post
defScale    = 1.0
printFormat = PNG 	#TIFF, PS, EPS, PNG, SVG
fieldIntervals = 30
animeFrameRate = 5


modelName   = 'simpleBlast'

#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.shell as shell
reload(func)
reload(shell)


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
	coordinates = (-10000.0, 100.0, 150.0), stepName=stepName)




#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(numIntervals=fieldIntervals)

#Delete default history output
del M.historyOutputRequests['H-Output-1']

#Create set
M.parts['Part-1'].Set(elements=
    M.parts['Part-1'].elements[32:33], name='middle')

#Create U history output
regionDef=M.rootAssembly.allInstances['Part-1-1'].sets['midNode']
M.HistoryOutputRequest(name='displacement', 
    createStepName=stepName, variables=('U1', ), region=regionDef, 
    sectionPoints=DEFAULT, rebar=EXCLUDE)

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

	#=========== Contour  ============#
	func.countourPrint(modelName, defScale, printFormat)

	#=========== Animation  ============#
	func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	#=========== XY  ============#
	shell.xySimpleDef(modelName, printFormat)

	print '   done'


print '###########    END OF SCRIPT    ###########'
