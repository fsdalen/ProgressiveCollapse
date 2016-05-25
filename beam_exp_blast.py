#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName     = 'beamBlast'
cpus        = 1			#Number of CPU's
monitor     = 0

run         = 1


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x           = 2			#Nr of columns in x direction
z           = 2			#Nr of columns in z direction
y           = 1			#nr of stories


#=========== Step  ============#
quasiTime   = 0.01 #3.0
blastTime   = 0.01 #0.1		#Takes around 0.03 for the wave to pass the building
freeTime    = 0.01 #2.0

qsSmoothFacor= 0.75	#When smooth step reaches full amplitude during QS step

precision   = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt    = SINGLE #SINGLE or FULL


#=========== General  ============#
#Live load
LL_kN_m     = -0.5	    #kN/m^2 (-2.0)

#Mesh
seed        = 750.0		#Global seed
slabSeedFactor = 1			#Change seed of slab

#Post
defScale    = 1.0
printFormat = PNG 		#TIFF, PS, EPS, PNG, SVG
animeFrameRate       = 5

quasiStaticIntervals = 5
blastIntervals       = 5
freeIntervals        = 5

blastCol             = 'COLUMN_B2-1'



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
func.perliminary(monitor, modelName)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
beam.buildBeamMod(modelName, x, z, y, seed, slabSeedFactor)



#=========== Quasi-static step  ============#

oldStep = 'Initial'
stepName = 'quasi-static'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=quasiTime)


#Create smooth step for forces
M.SmoothStepAmplitude(name='smooth', timeSpan=STEP, data=(
	(0.0, 0.0), (qsSmoothFacor*quasiTime, 1.0)))

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
dic = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4}
xBlast = dic[blastCol[7]]
zBlast = float(blastCol[8])-1
func.addIncidentWave(modelName, stepName,
	AmpFile= 'blastAmp.txt',
	sourceCo = (7500.0*xBlast + 10000.0, 500.0, 7500.0*zBlast),
	refCo = (7500.0*xBlast + 1000.0, 500.0, 7500.0*zBlast))


#Remove smooth step from other loads
M.loads['Gravity'].setValuesInStep(stepName=stepName, amplitude=FREED)
func.changeSlabLoad(M, x, z, y, stepName, amplitude=FREED)


#=========== Free step  ============#
#Create step
oldStep = stepName
stepName = 'free'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=freeTime)


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
M.fieldOutputRequests['F-Output-1'].setValuesInStep(
    stepName='free', numIntervals=freeIntervals)

#Field output: damage
M.FieldOutputRequest(name='damage', 
    createStepName='blast', variables=('SDEG', 'DMICRT', 'STATUS'),
    numIntervals=blastIntervals)
#Field output: damage
M.fieldOutputRequests['damage'].setValuesInStep(
    stepName='free', numIntervals=freeIntervals)


#Delete default history output
del M.historyOutputRequests['H-Output-1']


#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName='quasi-static', variables=('ALLIE', 'ALLKE', 'ALLWK'),
	numIntervals = quasiStaticIntervals)
M.historyOutputRequests['Energy'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)
M.historyOutputRequests['Energy'].setValuesInStep(
    stepName='free', numIntervals=freeIntervals)

#R2 at all col-bases
M.HistoryOutputRequest(createStepName='quasi-static', name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ),
	numIntervals = quasiStaticIntervals)
M.historyOutputRequests['R2'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)
M.historyOutputRequests['R2'].setValuesInStep(
    stepName='free', numIntervals=freeIntervals)

#U2 at top of column closes to blast
M.HistoryOutputRequest(name=blastCol+'_top'+'U', 
		createStepName='quasi-static', variables=('U1','U2','U3'), 
		region=M.rootAssembly.allInstances[blastCol].sets['col-top'],
		numIntervals = quasiStaticIntervals)
M.historyOutputRequests[blastCol+'_top'+'U'].setValuesInStep(
    stepName='blast', numIntervals=blastIntervals)
M.historyOutputRequests[blastCol+'_top'+'U'].setValuesInStep(
    stepName='free', numIntervals=freeIntervals)

# #U2 at middle (seed750 slabfactor1)
# M.rootAssembly.Set(name='centerSlab', nodes=
#     M.rootAssembly.instances['SLAB_A1-1'].nodes[60:61])
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

	#Open ODB
	odb = func.open_odb(modelName)

	# #Contour
	# func.countourPrint(modelName, defScale, printFormat)

	# #Animation
	# func.animate(modelName, defScale, frameRate= animeFrameRate)

	#Energy
	func.xyEnergyPlot(modelName)

	#R2 at col base
	beam.xyColBaseR2(modelName,x,z)

	beam.xyUtopCol(modelName, blastCol)
	
	
	# #Force and displacement
	# beam.xyCenterU2_colBaseR2(modelName,x,z)

	
	print '   done'


print '###########    END OF SCRIPT    ###########'
