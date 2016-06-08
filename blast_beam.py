#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


modelName      = 'blastBeam'
cpus           = 8			#Number of CPU's

run            = 0

parameter      = 0
runPara        = 0



#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 4			#Nr of columns in x direction
z              = 4			#Nr of columns in z direction
y              = 5			#nr of stories


#=========== Step  ============#
quasiTime      = 3.0
blastTime      = 0.1		
freeTime       = 2.0

qsSmoothFacor  = 0.75	#When smooth step reaches full amplitude during QS step

blastCol       = 'COLUMN_D4-1'
blastAmp       = 'blastAmp.txt'

precision   = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt    = SINGLE #SINGLE or FULL


#=========== General  ============#
monitor        = 0			#Write status of job continusly in Abaqus CAE

#Live load
LL_kN_m        = -0.5	    #kN/m^2 (-2.0)

#Mesh
seed           = 150.0 		#Frame seed
slabSeed       = 750.0		#Slab seed
steelMatFile   = 'mat_7.5.inp'  #Damage parameter is a function of element size

#Post
defScale       = 1.0
printFormat    = PNG 		#TIFF, PS, EPS, PNG, SVG
animeFrameRate = 5

qsIntervals    = 100
blastIntervals = 100
freeIntervals  = 200

qsFieldIntervals    = 6
blastFieldIntervals = 22
freeFieldIntervals  = 22



#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.beam as beam
reload(func)
reload(beam)


mdbName     = 'blastBeam' 	#Name of .cae file


steel = 'DOMEX_S355'
concrete = 'Concrete'

#Set up model with materials
func.perliminary(monitor, modelName, steelMatFile)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry
beam.buildBeamMod(modelName, x, z, y, seed, slabSeed)



#=========== Quasi-static step  ============#

oldStep = 'Initial'
stepName = 'quasiStatic'
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
	AmpFile= blastAmp,
	sourceCo =  (7500.0*xBlast + 10000.0, 0.0, 7500.0*zBlast), 
	refCo =     (7500.0*xBlast +  1000.0, 0.0, 7500.0*zBlast)) 


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


#Detete default output
del M.fieldOutputRequests['F-Output-1']
del M.historyOutputRequests['H-Output-1']


#Displacement field output
M.FieldOutputRequest(name='U', createStepName='quasiStatic', 
    variables=('U', ))

#Status field output
M.FieldOutputRequest(name='Status', createStepName='quasiStatic', 
    variables=('STATUS', ))


#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName='quasiStatic', variables=('ALLIE', 'ALLKE'))

#R2 at all col-bases
M.HistoryOutputRequest(createStepName='quasiStatic', name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ))


#U2 at top of column closes to blast
M.HistoryOutputRequest(name=blastCol+'_top'+'U', 
		createStepName='quasiStatic', variables=('U1','U2','U3'), 
		region=M.rootAssembly.allInstances[blastCol].sets['col-top'],)


# #U2 at middle of slab (seed750 slabfactor1)
# M.rootAssembly.Set(name='centerSlab', nodes=
#     M.rootAssembly.instances['SLAB_A1-1'].nodes[60:61])
# M.HistoryOutputRequest(createStepName=stepName, name='U2', 
# 	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))


#Change frequency of output for all steps
func.changeHistoryOutputFreq(modelName,
	quasiStatic=qsIntervals, blast = blastIntervals, free=freeIntervals)
func.changeFieldOutputFreq(modelName,
	quasiStatic=qsFieldIntervals, blast = blastFieldIntervals,
	free=freeFieldIntervals)


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

	#U at top of col closes to blast
	beam.xyUtopCol(modelName, blastCol)
	
	
	# #Force and displacement
	# beam.xyCenterU2_colBaseR2(modelName,x,z)

	
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
		modelName = 'beamBlastSeed'+str(para)
		
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


		if runPara:
			#Run job

			mdb.saveAs(pathName = mdbName + '.cae')
			func.runJob(modelName)
			func.readStaFile(modelName, 'results.txt')



			#=========== Post proccesing  ============#

			print 'Post processing...'
			
			#Energy
			func.xyEnergyPlot(modelName)

			#R2 at col base
			beam.xyColBaseR2(modelName,x,z)

			#U at top of col closes to blast
			beam.xyUtopCol(modelName, blastCol)






print '###########    END OF SCRIPT    ###########'
