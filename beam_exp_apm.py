#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'beamExpAPM'
cpus           = 8			#Number of CPU's
monitor        = 0

run            = 1

parameter      = 0
forceCollapse  = 1



#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 4			#Nr of columns in x direction
z              = 4			#Nr of columns in z direction
y              = 5			#nr of stories


#=========== Static model  ============#
static_Type    = 'general' 	#'general' or 'riks'
static_InInc   = 0.1		# Initial increment
static_MinIncr = 1e-9
static_maxInc  = 50 		#Maximum number of increments for static step


#=========== Explicit APM model  ============#
APMName		   = 'beamAPexpForceCollapseD4f50t5' 			#name of APM model and job
APMcol         = 'COLUMN_D4-1'		#Column to be removed

qsTime         = 3.0 				#Quasi static time
qsSmoothFactor = 0.75				#How fast to apply load with smooth amp
rmvStepTime    = 20e-3				#How fast to remove column forces
dynStepTime    = 4.00			#Length of free dynamic step

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt = SINGLE #SINGLE or FULL



#=========== Force collapse  ============#
loadTime       = 5.0
loadFactor     = 50.0





#=========== General  ============#
#Live load
LL_kN_m        = -0.5	    #kN/m^2 (-2.0)

#Mesh
seed           = 750.0		#Global seed
slabSeedFactor = 1			#Change seed of slab

#Post
defScale       = 1.0
printFormat    = PNG 		#TIFF, PS, EPS, PNG, SVG
animeFrameRate = 40

qsIntervals    = 100
rmvIntervals   = 5
freeIntervals  = 200
loadIntervals  = 200


#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

#Import library
import lib.func as func
import lib.beam as beam
reload(func)
reload(beam)

modelName   = 'beamStatic'



#Set up model with materials
func.perliminary(monitor, modelName)

#
M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
beam.buildBeamMod(modelName, x, z, y, seed, slabSeedFactor)










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
func.addSlabLoad(M, x, z, y, stepName, LL)


#=========== Output  ============#
#Delete default history output
del M.historyOutputRequests['H-Output-1']

#R2 at all col-bases
M.HistoryOutputRequest(createStepName='static', name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ))

#Section forces at top of column to be removed in APM
func.historySectionForces(M, APMcol, stepName)

#U2 at top of column to later be removed
M.HistoryOutputRequest(name=APMcol+'_top'+'U', 
		createStepName=stepName, variables=('U2',), 
		region=M.rootAssembly.allInstances[APMcol].sets['col-top'])



#=========== Save and run  ============#
M.rootAssembly.regenerate()


#Create job
mdb.Job(model=modelName, name=modelName, numCpus=cpus, numDomains=cpus)

#Run job
if run:
	mdb.saveAs(pathName = mdbName + '.cae')
	func.runJob(modelName)
	#Write CPU time to file
	func.readMsgFile(modelName, 'results.txt')



#=========== Post  ============#
	print 'Post processing...'

	
	# #Contour
	# func.countourPrint(modelName, defScale, printFormat)

	# #Animation
	# func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	#R2 at col base
	beam.xyColBaseR2(modelName,x,z)

	#Displacement at colTop
	beam.xyAPMcolPrint(modelName, APMcol)

	
	print '   done'













#==================================================#
#==================================================#
#                   APM ANALYSIS                   #
#==================================================#
#==================================================#


#New naming
oldMod = modelName
modelName = APMName


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
	previous=oldStep, timePeriod=qsTime, nlgeom=ON)


#Create smooth step for forces
M.SmoothStepAmplitude(name='Smooth', timeSpan=STEP, data=(
(0.0, 0.0), (qsSmoothFactor*qsTime, 1.0)))

#Add Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
    distributionType=UNIFORM, field='', name='Gravity', amplitude='Smooth')

#Add live load
func.addSlabLoad(M, x, z, y, stepName, load = LL, 
	amplitude = 'Smooth')


#Frequency of field output
M.fieldOutputRequests['F-Output-1'].setValues(
	numIntervals=qsIntervals)
#Field output: damage
M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'),
    numIntervals=qsIntervals)



#Delete default history output
del M.historyOutputRequests['H-Output-1']

#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),
	numIntervals=qsIntervals)

#History output: U2 at top of column removal
M.HistoryOutputRequest(name=APMcol+'_top'+'U', 
	createStepName=stepName, variables=('U2',), 
	region=M.rootAssembly.allInstances[APMcol].sets['col-top'],
	numIntervals=qsIntervals)

#R2 at all col-bases
M.HistoryOutputRequest(createStepName=stepName, name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ),
	numIntervals=qsIntervals)







#Delete BC and add fores for column to be removed
func.replaceForces(M, x, z, APMcol, oldJob=oldMod,
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

#Set output frequency of step
func.setOutputIntervals(modelName,stepName, rmvIntervals)




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




#Set output frequency of step
func.setOutputIntervals(modelName,stepName, loadIntervals)





#=========== Force collapse   ============#
if forceCollapse:
	#Create new loading step
	oldStep = stepName
	stepName='loading'
	M.ExplicitDynamicsStep(name=stepName, timePeriod=loadTime,
		previous=oldStep)


	#Create linear amplitude
	M.TabularAmplitude(data=((0.0, 1.0), (loadTime, loadFactor)), 
	    name='linIncrease', smooth=SOLVER_DEFAULT, timeSpan=STEP)

	#Change amplitude of slab load in force step
	func.changeSlabLoad(M, x, z, y, stepName, amplitude='linIncrease')

	#Set output frequency of step
	func.setOutputIntervals(modelName,stepName, loadIntervals)




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

			
	# #Contour
	# func.countourPrint(modelName, defScale, printFormat)

	#Animation
	func.animate(modelName, defScale, frameRate= animeFrameRate)

	#Energy
	func.xyEnergyPlot(modelName)

	#R2 at col base
	beam.xyColBaseR2(modelName,x,z)

	#Displacement at colTop
	beam.xyAPMcolPrint(modelName, APMcol)


	print '   done'



#==============================================================#
#==============================================================#
#                   PARAMETER STUDY                            #
#==============================================================#
#==============================================================#

oldMod = modelName

if parameter:
		
	#=========== Seed  ============#
	paraLst = [1500, 500, 300]


	for para in paraLst:
		
		#New model
		modelName = 'beamAPexpSeed'+str(para)
		mdb.Model(name=modelName, objectToCopy=mdb.models[oldMod])
		M = mdb.models[modelName]	


		#=========== Change parameter  ============#
		
		beam.mesh(M, seed = para, slabSeedFactor=1.0)

		M.rootAssembly.regenerate()




		#=========== Create job and run  ============#
		
		#Create job
		mdb.Job(model=modelName, name=modelName,
		    numCpus=cpus, numDomains=cpus,
		    explicitPrecision=precision, nodalOutputPrecision=nodalOpt)


		#Run job

		mdb.saveAs(pathName = mdbName + '.cae')
		func.runJob(modelName)
		func.readStaFile(modelName, 'results.txt')



		#=========== Post proccesing  ============#

		print 'Post processing...'
				
		# #Contour
		# func.countourPrint(modelName, defScale, printFormat)

		# #Animation
		# func.animate(modelName, defScale, frameRate= animeFrameRate)

		#Energy
		func.xyEnergyPlot(modelName)

		#R2 at col base
		beam.xyColBaseR2(modelName,x,z)

		#Displacement at colTop
		beam.xyAPMcolPrint(modelName, APMcol)


print '###########    END OF SCRIPT    ###########'
