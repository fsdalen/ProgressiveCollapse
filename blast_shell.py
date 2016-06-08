#Abaqus modules
from abaqus import *
from abaqusConstants import *
from mesh import *

#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


modelName            = 'blastShellSeed15ton'
cpus                 = 8			#Number of CPU's

run                  = 1





#=========== Geometry  ============#
#Size 	4x4  x10(5)
x                    = 4			#Nr of columns in x direction
z                    = 4			#Nr of columns in z direction
y                    = 5			#nr of stories


#=========== Step  ============#
quasiTime            = 3.0
blastTime            = 2.1


qsSmoothFactor       = 0.75

TNT                  = 15.0	         #tons of tnt
blastCol             = 'D4-1'

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt  = SINGLE #SINGLE or FULL


#=========== General  ============#
monitor               = 0			#Write status of job continusly in Abaqus CAE

#Live load
LL_kN_m              = -0.5	        #kN/m^2 (-2.0)

#Mesh
seed                 = 150.0	    #Frame seed
slabSeed     		 = 750			#Slabseed
steelMatFile   = 'mat_15.inp'  #Damage parameter is a function of element size

#Post
defScale             = 1.0
printFormat          = PNG 		     #TIFF, PS, EPS, PNG, SVG
animeFrameRate       = 40

qsIntervals          = 100
blastIntervals       = 300

qsFieldIntervals     = 6
blastFieldIntervals  = 44

#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.shell as shell
reload(func)
reload(shell)


mdbName = 'blastShell'


steel = 'DOMEX_S355'
concrete = 'Concrete'
rebarSteel = steel

#Set up model with materials
func.perliminary(monitor, modelName,steelMatFile)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#=========== Geometry  ============#
shell.createShellmod(modelName, x, z, y,seed, slabSeed)



#=========== Quasi-static step  ============#

oldStep = 'Initial'
stepName = 'quasiStatic'
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
	coordinates = (7500.0*xBlast + 10000.0, 0.0, 7500.0*zBlast),
	timeOfBlast = quasiTime, stepName=stepName)

#Remove smooth step from other loads
loads = M.loads.keys()
for load in loads:
	M.loads[load].setValuesInStep(stepName=stepName, amplitude=FREED)



M.rootAssembly.regenerate()

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

# #Status field output
# M.FieldOutputRequest(name='Status', createStepName='quasiStatic', 
#     variables=('STATUS', ))


#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName='quasiStatic', variables=('ALLIE', 'ALLKE'),)

#R2 history at colBases
M.HistoryOutputRequest(createStepName='quasiStatic', name='R2',
	region=M.rootAssembly.allInstances['FRAME-1'].sets['colBot'],
    variables=('RF2', ))

#U at top of column blastCol
shell.histColTopU(modelName, stepName='quasiStatic', column=blastCol)
M.historyOutputRequests['colTopU'].setValuesInStep(
    stepName='quasiStatic')


# #U2 at slab center (A1-1 slab)
# M.rootAssembly.Set(name='centerSlab', nodes=
#     M.rootAssembly.instances['SLAB-1'].nodes[24:25])
# M.HistoryOutputRequest(createStepName=stepName, name='U2', 
# 	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))



#Change frequency of output for all steps
func.changeHistoryOutputFreq(modelName,
	quasiStatic=qsIntervals, blast = blastIntervals)
func.changeFieldOutputFreq(modelName,
	quasiStatic=qsFieldIntervals, blast = blastFieldIntervals)


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
	#func.animate(modelName, defScale, frameRate= animeFrameRate)

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