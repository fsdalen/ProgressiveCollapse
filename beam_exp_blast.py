#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName     = 'beamQS'
cpus        = 1			#Number of CPU's
monitor     = 1

run         = 1


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x           = 2			#Nr of columns in x direction
z           = 2			#Nr of columns in z direction
y           = 1			#nr of stories


#=========== Step  ============#
quasiTime   = 2.0
blastTime   = 0.1
freeTime    = 0.5

precision   = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt    = SINGLE #SINGLE or FULL


#=========== General  ============#
#Live load
LL_kN_m     = -2.0	    #kN/m^2 (-2.0)

#Mesh
seed        = 750.0		#Global seed
slabSeedFactor = 1			#Change seed of slab

#Post
defScale    = 1.0
printFormat = PNG 		#TIFF, PS, EPS, PNG, SVG
animeFrameRate       = 5

quasiStaticIntervals = 100
blastIntervals       = 1000
freeIntervals        = 100




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
	(0.0, 0.0), (0.9*quasiTime, 1.0)))

#Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
	distributionType=UNIFORM, field='', name='Gravity',
	amplitude = 'smooth')

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
func.addSlabLoad(M, x, z, y, stepName, LL, amplitude = 'smooth')



# #=========== Blast step  ============#
# #Create step
# oldStep = stepName
# stepName = 'blast'
# M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
#     timePeriod=blastTime)

# #Join surfaces to create blastSurf
# lst = []
# for inst in M.rootAssembly.instances.keys():
# 	if inst.startswith('BEAM') or inst.startswith('COLUMN'):
# 		lst.append(M.rootAssembly.instances[inst].surfaces['surf'])
# 	if inst.startswith('SLAB'):
# 		lst.append(M.rootAssembly.instances[inst].surfaces['botSurf'])
# blastSurf = tuple(lst)
# M.rootAssembly.SurfaceByBoolean(name='blastSurf', surfaces=blastSurf)

# #Create blast
# func.addIncidentWave(modelName, stepName,
# 	sourceCo = (-10000.0, 500.0, 2000.0),
# 	refCo = (-1000.0, 500.0, 2000.0))


# #Remove smooth step from other loads
# M.loads['Gravity'].setValuesInStep(stepName=stepName, amplitude=FREED)
# func.changeSlabLoad(M, x, z, y, stepName, amplitude=FREED)


# # #=========== Free step  ============#
# #Create step
# oldStep = stepName
# stepName = 'free'
# M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
#     timePeriod=freeTime)


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
# M.fieldOutputRequests['F-Output-1'].setValuesInStep(
#     stepName='free', numIntervals=freeIntervals)

# #Field output: damage
# M.FieldOutputRequest(name='damage', 
#     createStepName='blast', variables=('SDEG', 'DMICRT', 'STATUS'),
#     numIntervals=blastIntervals)
# #Field output: damage
# M.fieldOutputRequests['damage'].setValuesInStep(
#     stepName='free', numIntervals=freeIntervals)


#Delete default history output
del M.historyOutputRequests['H-Output-1']


#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName='quasi-static', variables=('ALLIE', 'ALLKE', 'ALLWK'),
	numIntervals = quasiStaticIntervals)

#R2 at all col-bases
M.HistoryOutputRequest(createStepName='quasi-static', name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ),
	numIntervals = quasiStaticIntervals)

#U2 at middle (seed750 slabfactor1)
M.rootAssembly.Set(name='centerSlab', nodes=
    M.rootAssembly.instances['SLAB_A1-1'].nodes[60:61])
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

	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]

	# #=========== Contour  ============#
	# func.countourPrint(modelName, defScale, printFormat)

	# #=========== Animation  ============#
	# func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	#Energy
	func.xyEnergyPrint(modelName, printFormat)

	#R2 at column base
	beam.xyR2colBase(modelName, x,z, printFormat)
	
	#U2 at center slab
	plotName='U2centerSlab'
	odb=func.open_odb(modelName)
	xy1 = xyPlot.XYDataFromHistory(odb=odb, outputVariableName=
    	'Spatial displacement: U2 PI: SLAB_A1-1 Node 61 in NSET CENTERSLAB')
	c1 = session.Curve(xyData=xy1)
	func.XYprint(modelName, plotName, printFormat, c1)
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy1, ))
	func.fixReportFile(tempFile, plotName, modelName,
		xVar='Displacement [mm]', yVar ='Time [s]')

	
	print '   done'


print '###########    END OF SCRIPT    ###########'
