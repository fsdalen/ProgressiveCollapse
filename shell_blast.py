#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName              = 'shellQS'
cpus                 = 1			#Number of CPU's
monitor              = 1

run                  = 1


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x                    = 2			#Nr of columns in x direction
z                    = 2			#Nr of columns in z direction
y                    = 1			#nr of stories


#=========== Step  ============#
quasiTime            = 4.0
blastTime            = 1.0

qsSmoothFactor       = 0.75

TNT                  = 1.0	#tonns of tnt

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt = SINGLE #SINGLE or FULL


#=========== General  ============#
#Live load
LL_kN_m              = -2.0	    #kN/m^2 (-2.0)

#Mesh
seed                 = 150.0		#Global seed
slabSeedFactor 		 = 8			#Change seed of slab

#Post
defScale             = 1.0
printFormat          = PNG 		#TIFF, PS, EPS, PNG, SVG
quasiStaticIntervals = 1000
blastIntervals       = 100
animeFrameRate       = 10



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
rebarSteel = steel

#Set up model with materials
func.perliminary(monitor, modelName)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#=========== Geometry  ============#
shell.createShellmod(modelName, x, z, y,seed, slabSeedFactor)



#=========== Quasi-static step  ============#

oldStep = 'Initial'
stepName = 'quasi-static'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=quasiTime)


#Create smooth step for forces
M.SmoothStepAmplitude(name='smooth', timeSpan=STEP, data=(
	(0.0, 0.0), (qsSmoothFactor*quasiTime, 1.0)))

#Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
	distributionType=UNIFORM, field='', name='Gravity',
	amplitude = 'smooth')

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
shell.surfaceTraction(modelName,stepName, x, z, y, load=LL, amp='smooth')


# #=========== Blast step  ============#
# #Create step
# oldStep = stepName
# stepName = 'blast'
# M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
#     timePeriod=blastTime)


# #Create blast
# func.addConWep(modelName, TNT = TNT, blastType=SURFACE_BLAST,
# 	coordinates = (-10000.0, 0.0, 2000.0),
# 	timeOfBlast = quasiTime, stepName=stepName)

# #Remove smooth step from other loads
# loads = M.loads.keys()
# for load in loads:
# 	M.loads[load].setValuesInStep(stepName=stepName, amplitude=FREED)


M.rootAssembly.regenerate()

#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#


#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(
	numIntervals=quasiStaticIntervals)
# M.fieldOutputRequests['F-Output-1'].setValuesInStep(
#     stepName='blast', numIntervals=blastIntervals)

# #Damage field output
# M.FieldOutputRequest(name='damage', 
#     createStepName='blast', variables=('SDEG', 'DMICRT', 'STATUS'),
#     numIntervals=blastIntervals)

#Delete default history output
del M.historyOutputRequests['H-Output-1']

#Energy
M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),)

#R2 history at colBases
M.HistoryOutputRequest(createStepName=stepName, name='R2',
	region=M.rootAssembly.allInstances['FRAME-1'].sets['colBot'],
    variables=('RF2', ))

#U2 at shell center
M.rootAssembly.Set(name='centerSlab', nodes=
    M.rootAssembly.instances['SLAB-1'].nodes[24:25])
M.HistoryOutputRequest(createStepName=stepName, name='U2', 
	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))



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

	# #Contour
	# func.countourPrint(modelName, defScale, printFormat)

	# #Animation
	# func.animate(modelName, defScale, frameRate= animeFrameRate)

	#Energy
	func.xyEnergyPlot(modelName)


	# #R2 at column base
	# shell.xyR2colBase(modelName, x,z, printFormat)
	
	#Force and displacement
	shell.xyCenterU2_colBaseR2(modelName,x,z)
	
	print '   done'
