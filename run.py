#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName      = 'Explicit'
cpus         = 1			#Number of CPU's
monitor      = 1


#4x4  x10(5)
x            = 2			#Nr of columns in x direction
z            = 2			#Nr of columns in z direction
y            = 1			#nr of stories


#=========== Static  ============#
runStatic    = 0
staticPost   = 0			#Run post prossesing


staticType   = 'general' 	#'general' or 'riks'
nlg          = ON				# Nonlinear geometry (ON/OFF)
inInc        = 0.1				# Initial increment
minIncr      = 1e-9
maxStaticInc = 50 #Maximum number of increments for static step


#=========== APM  ============#
APM           = 0
runAPM        = 0
APMpost 	  = 0

APMcol        = 'COLUMN_B2-1'		#Column to be removed
histIntervals = 200 		#History output evenly spaced over n increments
staticTime    = 1.0				#Also used in Blast
rmvStepTime   = 1e-3
dynStepTime   = 1.0				



#=========== Blast  ============#
blast      = 1
runBlast   = 0
blastPost  = 0
staticTime = staticTime
blastTime  = 2.0



#=========== General  ============#
#Live load
LL_kN_m      = -2.0	    #kN/m^2 (-2.0)

#Post
defScale = 10
printFormat = PNG 	#TIFF, PS, EPS, PNG, SVG

#Explicit precision
precision = SINGLE #SINGLE, DOUBLE, DOUBLE_CONSTRAINT_ONLY or DOUBLE_PLUS_PACK
nodelOutp = SINGLE #SINGLE or FULL



#============================================================#
#============================================================#
#                   PERLIMINARIES                            #
#============================================================#
#============================================================#



#=========== Import modules  ============#

import os
import glob
from datetime import datetime

import ProgressiveCollapse.myFuncs as myFuncs
reload(myFuncs)


#=========== Other stuff  ============#

#Makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,
	recoverGeometry=COORDINATE)

#Print begin script to console
print '\n'*6
print '###########    NEW SCRIPT    ###########'
print str(datetime.now())[:19]

#Print status to console during analysis
if monitor:
	myFuncs.printStatus(ON)

#Create text file to write results in
with open('results.txt', 'w') as f:
	None






#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#


#=========== Set up model  ============#
modelName = "staticMod"
matFile = 'ProgressiveCollapse/mat_1.inp'

#Create model based on input material
print '\n'*2
mdb.ModelFromInputFile(name=modelName, inputFileName=matFile)
print '\n'*2

#For convinience
M = mdb.models[modelName]

#Deletes all other models
myFuncs.delModels(modelName)

#Close and delete old jobs and ODBs
myFuncs.delJobs(exeption = matFile)


#=========== Material  ============#
#Material names
steel = 'DOMEX_S355'
concrete = 'Concrete'
rebarSteel = 'Rebar Steel'

myFuncs.createMaterials(M, mat1=steel, mat2=concrete, mat3=rebarSteel)


#=========== Parts  ============#
#Create Column
col_height = 4000.0
myFuncs.createColumn(M, height=col_height, mat=steel, partName='COLUMN')

#Create Beam
beam_len = 8000.0
myFuncs.createBeam(M, length=beam_len, mat=steel, partName='BEAM')

#Create slab
myFuncs.createSlab(M, t=200.0, mat=concrete, dim=beam_len,
	rebarMat=rebarSteel, partName='SLAB')


#=========== Sets and surfaces  ============#
#A lot of surfaces are created with the joints
myFuncs.createSets(M, col_height)
myFuncs.createSurfs(M)


#=========== Assembly  ============#
myFuncs.createAssembly(M, x, z, y,
	x_d = beam_len, z_d = beam_len, y_d = col_height)


#=========== Mesh  ============#
seed = 800.0
myFuncs.mesh(M, seed)

#Write nr of elements to results file
M.rootAssembly.regenerate()
nrElm = myFuncs.elmCounter(M)
with open('results.txt','a') as f:
	f.write("%s	Elements: %s \n" %(modelName, nrElm))


#=========== Joints  ============#
myFuncs.createJoints(M, x, z, y,
	x_d = beam_len, z_d = beam_len, y_d = col_height)


#=========== Fix column base  ============#
myFuncs.fixColBase(M, x, z)




#===================================================#
#===================================================#
#               STEP AND DEPENDENCIES           	#
#===================================================#
#===================================================#

#=========== Static step  ============#
oldStep = 'Initial'
stepName = 'staticStep'

if staticType == 'general':
	M.StaticStep(name=stepName, previous=oldStep, 
		nlgeom=nlg,
		initialInc=inInc, minInc=minIncr, maxNumInc=maxStaticInc)
elif staticType == 'riks':
	M.StaticRiksStep(name=stepName, previous=oldStep, 
		nlgeom=nlg,
		initialArcInc=inInc, minArcInc=minIncr, maxNumInc=maxStaticInc,
		maxLPF=1.0)



#=========== History output  ============#
M.rootAssembly.regenerate()

#Delete default history output
del M.historyOutputRequests['H-Output-1']

#Energy
M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),)

#Section forces at top of column to be removed in APM
myFuncs.historySectionForces(M, APMcol, stepName)

#=========== Loads  ============#
# Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
    distributionType=UNIFORM, field='', name='Gravity')

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
myFuncs.addSlabLoad(M, x, z, y, stepName, load = LL)





#===========================================================#
#===========================================================#
#                   JOB ANS POST                            #
#===========================================================#
#===========================================================#

M.rootAssembly.regenerate()

#Create job
mdb.Job(model=modelName, name=modelName,
    numCpus=cpus, numDomains=cpus)

#Save mdb
mdb.saveAs(pathName = mdbName + '.cae')

#Run job
if runStatic:
	myFuncs.runJob(modelName)
	#Write CPU time and nr of incs to file
	myFuncs.readMsgFile(modelName, 'results.txt')


#=========== Post proccesing  ============#
if staticPost:

	print 'Post processing...'

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	#=========== Contour  ============#
	myFuncs.countourPrint(modelName, defScale, printFormat)

	#=========== XY  ============#
	myFuncs.xyEnergyPrint(modelName, printFormat)

	#=========== Animation  ============#
	myFuncs.animate(modelName, defScale, frameRate= 1)
	

	print '   done'





#==================================================#
#==================================================#
#                   APM                            #
#==================================================#
#==================================================#

if APM:

	#=========== Create APM model  ============#

	#New naming
	modelName = 'expAPM'
	stepName = 'quasi-staticStep'

	#Copy Model
	mdb.Model(name=modelName, objectToCopy=mdb.models['staticMod'])
	M = mdb.models[modelName]



	#=========== Quasi static step  ============#

	#Delete old static-step
	del M.steps['staticStep']

	#Create quasi-static step
	oldStep = 'Initial'
	M.ExplicitDynamicsStep(name=stepName, 
		previous=oldStep, timePeriod=staticTime, nlgeom=ON)


	#Create smooth step for forces
	M.SmoothStepAmplitude(name='Smooth', timeSpan=STEP, data=(
	(0.0, 0.0), (0.9*staticTime, 1.0)))

	#Add Gravity
	M.Gravity(comp2=-9800.0, createStepName=stepName, 
	    distributionType=UNIFORM, field='', name='Gravity', amplitude='Smooth')

	#Add live load
	myFuncs.addSmoothSlabLoad(M, x, z, y, stepName, load = LL, amplitude = 'Smooth')

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
	myFuncs.replaceForces(M, APMcol, oldJob='staticMod',
		oldStep = 'staticStep', stepName =stepName, amplitude='Smooth')




	#=========== Removal step  ============#
	oldStep = stepName
	stepName='forceRmvStep'
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
	stepName='dynamicStep'
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
	    explicitPrecision=precision, nodalOutputPrecision=nodelOutp)

	mdb.saveAs(pathName = mdbName + '.cae')

	#Run job
	if runAPM:
		myFuncs.runJob(modelName)
		myFuncs.explicitCPUtime(modelName, 'results.txt')


	#=========== Post proccesing  ============#
	if APMpost:

		print 'Post processing...'

		#Clear plots
		for plot in session.xyPlots.keys():
			del session.xyPlots[plot]

		#=========== Contour  ============#
		myFuncs.countourPrint(modelName, defScale, printFormat)

		#=========== XY  ============#
		myFuncs.xyEnergyPrint(modelName, printFormat)

		print '   done'





#====================================================#
#====================================================#
#                   Blast                            #
#====================================================#
#====================================================#


if blast:
	
	airDensity = 1.225e-12    #1.225 kg/m^3
	soundSpeed =340.29e3    # 340.29 m/s
	beamDrag = 1.15	#latteralMassCoef is for rectangle from wikipedia

	#=========== Create balst model  ============#
	modelName = 'blastMod'

	#Copy Model
	mdb.Model(name=modelName, objectToCopy=mdb.models['staticMod'])
	M = mdb.models[modelName]
	ass = M.rootAssembly



	#=========== Quasi static step  ============#
	stepName = 'quasi-staticStep'

	#Delete old static-step
	del M.steps['staticStep']

	#Create quasi-static step
	oldStep = 'Initial'
	M.ExplicitDynamicsStep(name=stepName, 
		previous=oldStep, timePeriod=staticTime, nlgeom=ON)

	#Create smooth step for forces
	M.SmoothStepAmplitude(name='Smooth', timeSpan=STEP, data=(
	(0.0, 0.0), (0.9*staticTime, 1.0)))

	#Add Gravity
	M.Gravity(comp2=-9800.0, createStepName=stepName, 
	    distributionType=UNIFORM, field='', name='Gravity', amplitude='Smooth')

	#Add live load
	myFuncs.addSmoothSlabLoad(M, x, z, y, stepName, load = LL, amplitude = 'Smooth')

	#Delete default history output
	del M.historyOutputRequests['H-Output-1']

	#History output: energy
	M.HistoryOutputRequest(name='Energy', 
		createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),
		numIntervals=histIntervals)

	#Field output: damage
	M.FieldOutputRequest(name='damage', 
	    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'))



	#=========== Blast step  ============#

	#Create blast step
	oldStep = stepName
	stepName = 'blastStep'
	M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
	timePeriod=blastTime)

	#Create pressure amplitude	
	myFuncs.createBlastAmp(M)

	#Create reference points
	myFuncs.createRPs(M,
		source=(-10.0e3, 2000, 4000.0),
		standoff =(-1000.0, 2000.0, 4000.0))

	#Create a blast surface
	myFuncs.blastSurf(M)

	#Create interaction property
	M.IncidentWaveProperty(name='Blast', 
	    definition=SPHERICAL, fluidDensity=airDensity, soundSpeed=soundSpeed)

	#Create incident Wave Interaction
	M.IncidentWave(name='Blast', createStepName=stepName, 
	    sourcePoint=ass.sets['Source'], standoffPoint=ass.sets['Standoff'],
	    surface=ass.surfaces['blastSurf'],
	    definition=PRESSURE, interactionProperty='Blast', 
	    referenceMagnitude=1.0, amplitude='Blast')

	#Fluid inertia of column
	M.sections['HEB550'].setValues(useFluidInertia=ON, fluidMassDensity=airDensity,
		crossSectionRadius=300.0, lateralMassCoef=beamDrag) 
		
	##Fluid inertia of beam
	M.sections['HUP300x300'].setValues(useFluidInertia=ON, fluidMassDensity=airDensity,
		crossSectionRadius=400.0, lateralMassCoef=beamDrag)

	#Set model wave formulation (must be set, but does not matter when fluid is not modeled)
	M.setValues(waveFormulation=TOTAL)



	#=========== Job  ============#
	
	M.rootAssembly.regenerate()

	#Create job
	mdb.Job(model=modelName, name=modelName,
	    numCpus=cpus, numDomains=cpus,
	    explicitPrecision=precision, nodalOutputPrecision=nodelOutp)

	mdb.saveAs(pathName = mdbName + '.cae')

	#Run job
	if runBlast:
		myFuncs.runJob(modelName)
		myFuncs.explicitCPUtime(modelName, 'results.txt')
	
	
	#=========== Post proccesing  ============#
	if blastPost:

		print 'Post processing...'

		#Clear plots
		for plot in session.xyPlots.keys():
			del session.xyPlots[plot]

		#=========== Contour  ============#
		myFuncs.countourPrint(modelName, defScale, printFormat)

		#=========== XY  ============#
		myFuncs.xyEnergyPrint(modelName, printFormat)

		print '   done'




print '###########    END OF SCRIPT    ###########'
