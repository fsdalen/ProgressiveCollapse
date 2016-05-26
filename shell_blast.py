#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName              = 'shellBlastSeed75'
cpus                 = 8			#Number of CPU's
monitor              = 0

run                  = 1



#=========== Geometry  ============#
#Size 	4x4  x10(5)
x                    = 4			#Nr of columns in x direction
z                    = 4			#Nr of columns in z direction
y                    = 5			#nr of stories


#=========== Step  ============#
quasiTime            = 3.0
blastTime            = 2.0
#freeTime			 = 0.1

qsSmoothFactor       = 0.75

TNT                  = 1.0	#tonns of tnt

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt  = SINGLE #SINGLE or FULL


#=========== General  ============#
#Live load
LL_kN_m              = -0.5	    #kN/m^2 (-2.0)

#Mesh
seed                 = 75.0		#Global seed
slabSeedFactor 		 = 8			#Change seed of slab

#Post
defScale             = 1.0
printFormat          = PNG 		#TIFF, PS, EPS, PNG, SVG

qsIntervals          = 40
blastIntervals       = 500
#freeIntervals		 = 20

animeFrameRate       = 40


blastCol             = 'D3-1'

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


#=========== Blast step  ============#
#Create step
oldStep = stepName
stepName = 'blast'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=blastTime)


#Create blast
#Read column name into x,y,z
dic = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4}
xBlast = dic[blastCol[0]]
zBlast = float(blastCol[1])-1
func.addConWep(modelName, TNT = TNT, blastType=SURFACE_BLAST,
	coordinates = (7500.0*xBlast + 10000.0, 500.0, 7500.0*zBlast),
	timeOfBlast = quasiTime, stepName=stepName)

#Remove smooth step from other loads
loads = M.loads.keys()
for load in loads:
	M.loads[load].setValuesInStep(stepName=stepName, amplitude=FREED)




#The free step after the blast step does not work for some stupid reason
#The analyis won't even start because of some amplitude defenition is not found
# #=========== Free step  ============#
# #Create step
# oldStep = stepName
# stepName = 'free'
# M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
#     timePeriod=freeTime)
# M.ExplicitDynamicsStep(name='Step-3', previous='blast')




M.rootAssembly.regenerate()

#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#


#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(
	numIntervals=qsIntervals)
M.fieldOutputRequests['F-Output-1'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)
# M.fieldOutputRequests['F-Output-1'].setValuesInStep(
#     stepName='free', numIntervals=freeIntervals)

#Field output: damage
M.FieldOutputRequest(name='damage', 
    createStepName='blast', variables=('SDEG', 'DMICRT', 'STATUS'),
    numIntervals=blastIntervals)
#Field output: damage
# M.fieldOutputRequests['damage'].setValuesInStep(
#     stepName='free', numIntervals=freeIntervals)


#Delete default history output
del M.historyOutputRequests['H-Output-1']


#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName='quasi-static', variables=('ALLIE', 'ALLKE', 'ALLWK'),
	numIntervals = qsIntervals)
M.historyOutputRequests['Energy'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)
# M.historyOutputRequests['Energy'].setValuesInStep(
#     stepName='free', numIntervals=freeIntervals)

#R2 history at colBases
M.HistoryOutputRequest(createStepName='quasi-static', name='R2',
	region=M.rootAssembly.allInstances['FRAME-1'].sets['colBot'],
    variables=('RF2', ))
M.historyOutputRequests['R2'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)
# M.historyOutputRequests['R2'].setValuesInStep(
#     stepName='free', numIntervals=freeIntervals)

#U at top of column blastCol
shell.histColTopU(modelName, stepName='quasi-static', column=blastCol)
M.historyOutputRequests['colTopU'].setValuesInStep(
    stepName='quasi-static', numIntervals=blastIntervals)
M.historyOutputRequests['colTopU'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)
# M.historyOutputRequests['colTopU'].setValuesInStep(
#     stepName='free', numIntervals=freeIntervals)


# #U2 at slab center (A1-1 slab)
# M.rootAssembly.Set(name='centerSlab', nodes=
#     M.rootAssembly.instances['SLAB-1'].nodes[24:25])
# M.HistoryOutputRequest(createStepName=stepName, name='U2', 
# 	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))



#===========================================================#
#===========================================================#
#                   Save and run                            #
#===========================================================#
#===========================================================#
M.rootAssembly.regenerate()

#Create job
mdb.Job(model=modelName, name=modelName, numCpus=cpus, numDomains=cpus,
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

	#Animation
	func.animate(modelName, defScale, frameRate= animeFrameRate)

	#Energy
	func.xyEnergyPlot(modelName)

	#R2 at column base
	shell.xyR2colBase(modelName, x,z)

	#U at column top
	shell.xyUcolTop(modelName, column=blastCol)
	
	# #Force and displacement
	# shell.xyCenterU2_colBaseR2(modelName,x,z)
	
	print '   done'








print '###########    END OF SCRIPT    ###########'