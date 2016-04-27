#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName      = 'Implicit'
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




#================ APM ==================#
#Single APM
APM           = 1
runAPM        = 1
APMpost       = 1
multiAPM      = 1	#This includes run and post for multi

APMcol        = 'COLUMN_B2-1'
rmvStepTime   = 1e-3		#Also used in MuliAPM (Fu uses 20e-3)
dynStepTime   = 0.1


#Data extraction for multiAPM
elsetName     = None
var           = 'PEEQ' #'S'
var_invariant = None #'mises'
limit         = 0.1733	#Correct limit for PEEQ = 0.1733



#=========== General  ============#


#Live load
LL_kN_m      = -2.0	    #kN/m^2 (-2.0)


#Post
defScale = 10
printFormat = PNG 	#TIFF, PS, EPS, PNG, SVG





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

#Create history output for energies
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
#                   JOB AND POST                            #
#===========================================================#
#===========================================================#

M.rootAssembly.regenerate()

#Save model
mdb.saveAs(pathName = mdbName + '.cae')

#Create job
mdb.Job(model=modelName, name=modelName,
    numCpus=cpus)

#Run job
if runStatic:
	myFuncs.runJob(modelName)
	#Write CPU time to file
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

	#Create new model
	modelName = 'APM'
	mdb.Model(name=modelName, objectToCopy=mdb.models['staticMod'])	
	M = mdb.models[modelName]

	# Create step for column removal
	oldStep = 'staticStep'
	stepName = 'elmRemStep'
	M.ImplicitDynamicsStep( name=stepName,  previous=oldStep, 
		initialInc=rmvStepTime, maxNumInc=50,
		timeIncrementationMethod=FIXED, timePeriod=rmvStepTime,
		nlgeom=nlg)

	#Remove column
	rmvSet = APMcol+'.set'
	M.ModelChange(activeInStep=False, createStepName=stepName, 
		includeStrain=False, name='elmRemoval', region=
		M.rootAssembly.sets[rmvSet], regionType=GEOMETRY)
	
	#Create dynamic APM step
	oldStep = stepName
	stepName = 'dynamicStep'
	M.ImplicitDynamicsStep(initialInc=0.01, minInc=5e-05, name=
		stepName, previous=oldStep, timePeriod=dynStepTime, nlgeom=nlg,
		maxNumInc=300)



	#=========== Job  ============#
	
	M.rootAssembly.regenerate()

	#Save model
	mdb.saveAs(pathName = mdbName + '.cae')

	#Create job
	mdb.Job(model=modelName, name=modelName,
	    numCpus=cpus, numDomains=cpus,
	    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE)

	#Run job
	if runAPM:
		myFuncs.runJob(modelName)
		#Write CPU time to file
		myFuncs.staticCPUtime(modelName, 'results.txt')


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

		#=========== Animation  ============#
		myFuncs.animate(modelName, defScale, frameRate= 1)
		mdb.saveAs(pathName = mdbName+'.cae')

	


#========================================================#
#========================================================#
#                   MULTI APM                            #
#========================================================#
#========================================================#



if multiAPM:
		
	#Original Names
	originModel = modelName		#oldModel = modelName
	originLastStep = stepName 	#oldStep = stepName


	#Check original ODB
	print '\n' + "Getting data from ODB..."
	elmOverLim = myFuncs.getElmOverLim(originModel, var,
		originLastStep, var_invariant, limit)
	print "    done"
	if not elmOverLim: print 'No element over limit'

	#Run itterations
	count = 0
	while len(elmOverLim) > 0:
		count = count + 1
		
		#New names
		modelName = 'multiAPM_'+str(count)
		

		#Copy new model
		mdb.Model(name=modelName, objectToCopy=mdb.models[originModel])	
		M = mdb.models[modelName]

		#Create step for element removal
		stepName = 'elmRmvStep'
		M.rootAssembly.regenerate()
		M.ImplicitDynamicsStep(initialInc=rmvStepTime, maxNumInc=50, name=
			stepName, noStop=OFF, nohaf=OFF, previous=originLastStep, 
			timeIncrementationMethod=FIXED, timePeriod=rmvStepTime, nlgeom=nlg)

		myFuncs.delInstance(M, elmOverLim, stepName)

		#================ Create new step and job =============#
		#Create dynamic APM step
		oldStep = stepName
		stepName = 'implicitStep'
		M.ImplicitDynamicsStep(initialInc=0.01, minInc=5e-05, name=
			stepName, previous=oldStep, timePeriod=dynStepTime, nlgeom=nlg,
			maxNumInc=300)

		#Create job
		mdb.Job(model=modelName, name=modelName,
    		numCpus=cpus, numDomains=cpus)
		
		#Save model
		mdb.saveAs(pathName = caeName+'.cae')
		
		#Run job
		myFuncs.runJob(modelName)
		#Write CPU time to file
		myFuncs.staticCPUtime(modelName, 'results.txt')

		#================ Check new ODB ==========================#
		oldODB = modelName
		print '\n' + "Getting data from ODB..."
		elmOverLim = myFuncs.getElmOverLim(modelName, var,
			originLastStep, var_invariant, limit)
		print "    done"
		if len(elmOverLim) == 0:
			print 'Req	uired itterations: %s' % (count)



print '###########    END OF SCRIPT    ###########'
