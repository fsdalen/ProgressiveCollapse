#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'beamBlast'
cpus           = 1			#Number of CPU's
monitor        = 1

run            = 0


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 2			#Nr of columns in x direction
z              = 2			#Nr of columns in z direction
y              = 1			#nr of stories


#=========== Step  ============#
quasiTime	   = 0.5
blastTime 	   = 0.1

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt = SINGLE #SINGLE or FULL


#=========== General  ============#
#Live load
LL_kN_m        = -2.0	    #kN/m^2 (-2.0)

#Mesh
seed           = 150.0		#Global seed

#Post
defScale       = 1.0
printFormat    = PNG 		#TIFF, PS, EPS, PNG, SVG
quasiStaticIntervals = 10
blastIntervals       = 100
animeFrameRate = 5



#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.beam as beam
reload(func)
reload(beam)

modelName   = mdbName

steel = 'DOMEX_S355'
concrete = 'Concrete'
rebarSteel = steel

#Set up model with materials
func.perliminary(monitor, modelName, steel, concrete)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
beam.buildBeamMod(modelName, x, z, y, steel, concrete, rebarSteel, seed)



#=========== Quasi-static step  ============#

oldStep = 'Initial'
stepName = 'quasi-static'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=quasiTime)


#Create smooth step for forces
M.SmoothStepAmplitude(name='smooth', timeSpan=STEP, data=(
	(0.0, 0.0), (0.9*quasiTime, 1.0)))

#Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
	distributionType=UNIFORM, field='', name='Gravity',
	amplitude = 'smooth')

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
func.addSlabLoad(M, x, z, y, stepName, LL, amplitude = 'smooth')



#=========== Blast step  ============#
#Create step
oldStep = stepName
stepName = 'blast'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=blastTime)

#Join surfaces to create blastSurf
lst = []
for inst in M.rootAssembly.instances.keys():
	if inst.startswith('BEAM') or inst.startswith('COLUMN'):
		lst.append(M.rootAssembly.instances[inst].surfaces['surf'])
	if inst.startswith('SLAB'):
		lst.append(M.rootAssembly.instances[inst].surfaces['botSurf'])
blastSurf = tuple(lst)
M.rootAssembly.SurfaceByBoolean(name='blastSurf', surfaces=blastSurf)

#Create blast
func.blast(modelName, stepName,
	sourceCo = (-10000.0, 500.0, 2000.0),
	refCo = (-1000.0, 500.0, 2000.0))


#Remove smooth step from other loads
M.loads['Gravity'].setValuesInStep(stepName=stepName, amplitude=FREED)
func.changeSlabLoad(M, x, z, y, stepName, amplitude=FREED)


#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(
	numIntervals=quasiStaticIntervals)
M.fieldOutputRequests['F-Output-1'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)

#Field output: damage
M.FieldOutputRequest(name='damage', 
    createStepName='blast', variables=('SDEG', 'DMICRT', 'STATUS'),
    numIntervals=blastIntervals)


#Delete default history output
del M.historyOutputRequests['H-Output-1']


#History output



#===========================================================#
#===========================================================#
#                   Save and run                            #
#===========================================================#
#===========================================================#
M.rootAssembly.regenerate()


#Create job
mdb.Job(model=modelName, name=modelName, numCpus=cpus,
	explicitPrecision=precision, nodalOutputPrecision=nodalOpt)

#Run job
if run:
	#Save model
	mdb.saveAs(pathName = mdbName + '.cae')
	#Run model
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
	
	print '   done'


print '###########    END OF SCRIPT    ###########'
