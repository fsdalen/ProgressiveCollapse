#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'beamImpAPM'
cpus           = 8			#Number of CPU's
monitor        = 0

run            = 1


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 4			#Nr of columns in x direction
z              = 4			#Nr of columns in z direction
y              = 4			#nr of stories


#=========== Static step  ============#
static_Type    = 'general' 	#'general' or 'riks'
static_InInc   = 0.1		# Initial increment
static_MinIncr = 1e-9
static_maxInc  = 50 		#Maximum number of increments for static step



#=========== Implicit step  ============#
#Single APM
APMcol        = 'COLUMN_D4-1'
rmvStepTime   = 20e-3		#Also used in MuliAPM (Fu uses 20e-3)
dynStepTime   = 2.0


#Itterations
itterations   = 0
elsetName     = None
var           = 'PEEQ' #'S'
var_invariant = None #'mises'
limit         = 0.1733	#Correct limit for PEEQ = 0.1733



#=========== General  ============#
#Live load
LL_kN_m        = -0.5	    #kN/m^2 (-2.0)

#Mesh
seed           = 750.0		#Global seed
slabSeedFactor = 1			#Change seed of slab

#Post
defScale       = 1.0
printFormat    = PNG 		#TIFF, PS, EPS, PNG, SVG
animeFrameRate = 5

rmvIntervals   = 5
freeIntervals  = 200


#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.beam as beam
reload(func)
reload(beam)

modelName   = 'beamAPimp'


#Set up model with materials
func.perliminary(monitor, modelName)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
beam.buildBeamMod(modelName, x, z, y, seed, slabSeedFactor)



#=========== Static step  ============#
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



# Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
	distributionType=UNIFORM, field='', name='Gravity')

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
func.addSlabLoad(M, x, z, y, stepName, LL)





#Field output: damage
M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'))

#Delete default history output
del M.historyOutputRequests['H-Output-1']

#Create history output for energies
M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),)

#R2 at all col-bases
M.HistoryOutputRequest(createStepName='static', name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ))

#Section forces at top of column to be removed in APM
func.historySectionForces(M, APMcol, stepName)

#U2 at top of column to later be removed
M.HistoryOutputRequest(name=APMcol+'_top'+'U', 
		createStepName=stepName, variables=('U2',), 
		region=M.rootAssembly.allInstances[APMcol].sets['col-top'])




#=========== Coulumn removal step  ============#

# Create step for column removal
oldStep = stepName
stepName = 'elmRemStep'
M.ImplicitDynamicsStep( name=stepName,  previous=oldStep, 
	initialInc=rmvStepTime, maxNumInc=50,
	timeIncrementationMethod=FIXED, timePeriod=rmvStepTime,
	nlgeom=ON)

#Remove column
rmvSet = APMcol+'.set'
M.ModelChange(activeInStep=False, createStepName=stepName, 
	includeStrain=False, name='elmRemoval', region=
	M.rootAssembly.sets[rmvSet], regionType=GEOMETRY)

#Set output frequency of step
func.setOutputIntervals(modelName,stepName, rmvIntervals)


#=========== Dynamic step  ============#

#Create dynamic APM step
oldStep = stepName
stepName = 'dynamicStep'
M.ImplicitDynamicsStep(initialInc=0.01, minInc=5e-05, name=
	stepName, previous=oldStep, timePeriod=dynStepTime, nlgeom=ON,
	maxNumInc=300)

#Set output frequency of step
func.setOutputIntervals(modelName,stepName, freeIntervals)



#=========== Save and run  ============#
M.rootAssembly.regenerate()

#Save model

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

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	#Contour
	func.countourPrint(modelName, defScale, printFormat)

	#Energy
	func.xyEnergyPlot(modelName)

	#R2 at col base
	beam.xyColBaseR2(modelName,x,z)

	#Displacement at colTop
	beam.xyAPMcolPrint(modelName, APMcol)
 

	#Check largest peeq against criteria
	print '\n' + "Getting data from ODB..."
	elmOverLim = func.getElmOverLim(modelName, var,
	stepName, var_invariant, limit)
	print "    done"
	with open('results.txt','a') as f:
		if elmOverLim:
			num = len(elmOverLim)
			f.write('%s	Nr of elements over lim: %s' %(modelName, num))
		else: 
			f.write('%s	No element over limit' %(modelName))




	print '   done'





#==========================================================#
#==========================================================#
#                   ITTERATIONS                            #
#==========================================================#
#==========================================================#
if itterations:

	#Original Names
	originModel = modelName
	originLastStep = stepName

	#Check original ODB
	print '\n' + "Getting data from ODB..."
	elmOverLim = func.getElmOverLim(originModel, var,
	originLastStep, var_invariant, limit)
	print "    done"
	if not elmOverLim: print 'No element over limit'

	#Run itterations
	count = 0
	while len(elmOverLim) > 0:
		count = count + 1

		#New names
		modelName = 'impAPM-'+str(count)


		#Copy new model
		mdb.Model(name=modelName, objectToCopy=mdb.models[originModel])	
		M = mdb.models[modelName]

		#Create step for element removal
		stepName = 'elmRmv'
		M.rootAssembly.regenerate()
		M.ImplicitDynamicsStep(initialInc=rmvStepTime, maxNumInc=50, name=
			stepName, noStop=OFF, nohaf=OFF, previous=originLastStep, 
			timeIncrementationMethod=FIXED, timePeriod=rmvStepTime, nlgeom=nlg)

		func.delInstance(M, elmOverLim, stepName)

		#================ Create new step and job =============#
		#Create dynamic APM step
		oldStep = stepName
		stepName = 'implicit'
		M.ImplicitDynamicsStep(initialInc=0.01, minInc=5e-05, name=
			stepName, previous=oldStep, timePeriod=dynStepTime, nlgeom=nlg,
			maxNumInc=300)

		#Create job
		mdb.Job(model=modelName, name=modelName, numCpus=cpus,)

		#Save model
		mdb.saveAs(pathName = caeName+'.cae')

		#Run job
		func.runJob(modelName)

		#Write CPU time to file
		func.readMsgFile(modelName, 'results.txt')

		#=========== Post  ============#
		#Clear plots
		for plot in session.xyPlots.keys():
			del session.xyPlots[plot]

		#Contour
		func.countourPrint(modelName, defScale, printFormat)

		#Energy
		func.xyEnergyPrint(modelName, printFormat)

		#U2 at top of removed column to be removed
		func.xyAPMcolPrint(modelName, APMcol, printFormat, stepName)

		#Animation
		func.animate(modelName, defScale, frameRate= 1)
		mdb.saveAs(pathName = mdbName+'.cae')


		#================ Check new ODB ==========================#
		oldODB = modelName
		print '\n' + "Getting data from ODB..."
		elmOverLim = func.getElmOverLim(modelName, var,
			originLastStep, var_invariant, limit)
		print "    done"
		if len(elmOverLim) == 0:
			print 'Req	uired itterations: %s' % (count)



print '###########    END OF SCRIPT    ###########'
