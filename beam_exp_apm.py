#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'beamExpAPM'
cpus           = 1			#Number of CPU's
monitor        = 1

run            = 1


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 2			#Nr of columns in x direction
z              = 2			#Nr of columns in z direction
y              = 1			#nr of stories


#=========== Static model  ============#
static_Type    = 'general' 	#'general' or 'riks'
static_InInc   = 0.1		# Initial increment
static_MinIncr = 1e-9
static_maxInc  = 50 		#Maximum number of increments for static step


#=========== Explicit model  ============#
APMcol        = 'COLUMN_B2-1'		#Column to be removed
histIntervals = 200 		#History output evenly spaced over n increments
staticTime    = 0.1				
rmvStepTime   = 1e-3
dynStepTime   = 0.1	

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
fieldIntervals = 30
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

modelName   = 'beamStatic'

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
beam.buildBeamMod(modelName, x, z, y, steel, concrete, rebarSteel)










#============================================================#
#============================================================#
#                   STATIC ANALYSIS                          #
#============================================================#
#============================================================#



#=========== Step  ============#
oldStep = 'Initial'
stepName = 'static'
if static_Type == 'general':
	M.StaticStep(name=stepName, previous=oldStep, 
		nlgeom=ON, initialInc=static_InInc, minInc=static_MinIncr,
		maxNumInc=static_maxInc)
elif static_Type == 'riks':
	M.StaticRiksStep(name=stepName, previous=oldStep, 
		nlgeom=ON, initialArcInc=static_InInc, minArcInc=static_MinIncr,
		maxNumInc=static_maxInc, maxLPF=1.0)



#=========== Loads  ============#
# Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
	distributionType=UNIFORM, field='', name='Gravity')

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
beam.addSlabLoad(M, x, z, y, stepName, LL)


#=========== Output  ============#
#Delete default history output
del M.historyOutputRequests['H-Output-1']


#Section forces at top of column to be removed in APM
beam.historySectionForces(M, APMcol, stepName)

#U2 at top of column to later be removed
M.HistoryOutputRequest(name=APMcol+'_top'+'U', 
		createStepName=stepName, variables=('U2',), 
		region=M.rootAssembly.allInstances[APMcol].sets['col-top'])



#=========== Save and run  ============#
M.rootAssembly.regenerate()

#Save model

#Create job
mdb.Job(model=modelName, name=modelName, numCpus=cpus)

#Run job
if run:
	mdb.saveAs(pathName = mdbName + '.cae')
	func.runJob(modelName)
	#Write CPU time to file
	func.readMsgFile(modelName, 'results.txt')



#=========== Post  ============#
	print 'Post processing...'

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	#Contour
	func.countourPrint(modelName, defScale, printFormat)

	#Animation
	func.animate(modelName, defScale, frameRate= animeFrameRate)

	#U2 at top of column to be removed
	beam.xyAPMcolPrint(modelName, APMcol, printFormat, stepName)

	
	print '   done'





#==================================================#
#==================================================#
#                   APM ANALYSIS                   #
#==================================================#
#==================================================#


#New naming
oldMod = modelName
modelName = 'beamExpAPM'


#Copy Model
mdb.Model(name=modelName, objectToCopy=mdb.models[oldMod])
M = mdb.models[modelName]



#=========== Quasi static step  ============#

#Delete old static-step
del M.steps[stepName]

#Create quasi-static step
oldStep = 'Initial'
stepName = 'quasiStatic'
M.ExplicitDynamicsStep(name=stepName, 
	previous=oldStep, timePeriod=staticTime, nlgeom=ON)



#Create smooth step for forces
M.SmoothStepAmplitude(name='Smooth', timeSpan=STEP, data=(
(0.0, 0.0), (0.9*staticTime, 1.0)))

#Add Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
    distributionType=UNIFORM, field='', name='Gravity', amplitude='Smooth')

#Add live load
beam.addSlabLoad(M, x, z, y, stepName, load = LL, 
	amplitude = 'Smooth')





#Delete default history output
del M.historyOutputRequests['H-Output-1']

#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),
	numIntervals=histIntervals)

#History output: U2 at top of column removal
M.HistoryOutputRequest(name=APMcol+'_top'+'U', 
	createStepName=stepName, variables=('U2',), 
	region=M.rootAssembly.allInstances[APMcol].sets['col-top'],
	sectionPoints=DEFAULT, rebar=EXCLUDE, numIntervals=histIntervals)

#Field output: damage
M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'))





#Delete BC and add fores for column to be removed
beam.replaceForces(M, APMcol, oldJob=oldMod,
	oldStep = 'static', stepName =stepName, amplitude='Smooth')






#=========== Removal step  ============#
oldStep = stepName
stepName='forceRmv'
M.ExplicitDynamicsStep(name=stepName, timePeriod=rmvStepTime,
	previous=oldStep)

#Create amplitude for force removal
M.TabularAmplitude(name='lin-dec', timeSpan=STEP, 
	smooth=SOLVER_DEFAULT, data=((0.0, 1.0), (1.0, 0.0)))

#Remove forces
M.loads['Forces'].setValuesInStep(stepName=stepName, amplitude='lin-dec')
M.loads['Moments'].setValuesInStep(stepName=stepName, amplitude='lin-dec')






#=========== Dynamic step  ============#

#Create APM step
oldStep = stepName
stepName='dynamic'
M.ExplicitDynamicsStep(name=stepName,timePeriod=dynStepTime,
	previous=oldStep)

#Set forces = 0 in last step
M.loads['Forces'].setValuesInStep(stepName=stepName,
	cf1=0.0, cf2=0.0, cf3=0.0, amplitude=FREED)
M.loads['Moments'].setValuesInStep(stepName=stepName,
	cm1=0.0, cm2=0.0, cm3=0.0, amplitude=FREED)





#=========== Job  ============#

#Create job
mdb.Job(model=modelName, name=modelName,
    numCpus=cpus, numDomains=cpus,
    explicitPrecision=precision, nodalOutputPrecision=nodalOpt)



#Run job
if run:
	mdb.saveAs(pathName = mdbName + '.cae')
	func.runJob(modelName)
	func.readStaFile(modelName, 'results.txt')


#=========== Post proccesing  ============#

	print 'Post processing...'

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	#=========== Contour  ============#
	func.countourPrint(modelName, defScale, printFormat)

	#=========== XY  ============#
	#Energy
	func.xyEnergyPrint(modelName, printFormat)

	#U2 at top of removed column
	beam.xyAPMcolPrint(modelName, APMcol, printFormat,
		stepName)

	print '   done'







print '###########    END OF SCRIPT    ###########'
