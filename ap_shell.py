#Abaqus modules
from abaqus import *
from abaqusConstants import *
from mesh import *

#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


modelName            = 'apShell'
cpus                 = 8			#Number of CPU's

run                  = 1





#=========== Geometry  ============#
#Size 	4x4  x10(5)
x                    = 4			#Nr of columns in x direction
z                    = 4			#Nr of columns in z direction
y                    = 5			#nr of stories


#=========== Explicit AP model  ============#
APMcol         = 'D4-1'		#Column to be removed

qsTime         = 3.0 		    	#Quasi static time
rmvStepTime    = 20e-3				#How fast to remove column forces
dynStepTime    = 2.00   	       #Length of free dynamic step (collapse:4.0)

qsSmoothFactor = 0.75				#How fast to apply load with smooth amp

precision = SINGLE #SINGLE/ DOUBLE/ DOUBLE_CONSTRAINT_ONLY/ DOUBLE_PLUS_PACK
nodalOpt = SINGLE #SINGLE or FULL



#=========== General  ============#
monitor               = 0			#Write status of job continusly in Abaqus CAE

#Live load
LL_kN_m              = -0.5	        #kN/m^2 (-2.0)

#Mesh
seed                 = 150		    #Global seed
slabSeed    		 = 750			#Change seed of slab
steelMatFile   = 'mat_15.inp'  #Damage parameter is a function of element size

#Post
defScale             = 1.0
printFormat          = PNG 		     #TIFF, PS, EPS, PNG, SVG
animeFrameRate       = 40

#History output intervals
qsIntervals    = 100
rmvIntervals   = 2
freeIntervals  = 200


#Field output intervals
qsFieldIntervals    = 6
rmvFieldIntervals   = 1
freeFieldIntervals  = 45


#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.shell as shell
reload(func)
reload(shell)


mdbName = 'apShell'


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
    timePeriod=qsTime)


#Create smooth step for forces
M.SmoothStepAmplitude(name='smooth', timeSpan=STEP, data=(
	(0.0, 0.0), (qsSmoothFactor*qsTime, 1.0)))

#Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
	distributionType=UNIFORM, field='', name='Gravity',
	amplitude = 'smooth')

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
shell.surfaceTraction(modelName,stepName, x, z, y, load=LL, amp='smooth')


#=========== Removal step  ============#
#Create step
oldStep = stepName
stepName = 'colRmv'
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=rmvStepTime)


#Remove smooth step from other loads
loads = M.loads.keys()
for load in loads:
	M.loads[load].setValuesInStep(stepName=stepName, amplitude=FREED)


#Remove bottom BC of APMcol
shell.rmvColBC(modelName, stepName, column=APMcol)




#=========== Free step  ============#
#Create APM step
oldStep = stepName
stepName='free'
M.ExplicitDynamicsStep(name=stepName,timePeriod=dynStepTime,
	previous=oldStep)


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

#U at top of column APMcol
shell.histColTopU(modelName, stepName='quasiStatic', column=APMcol)
M.historyOutputRequests['colTopU'].setValuesInStep(
    stepName='quasiStatic')


# #U2 at slab center (A1-1 slab)
# M.rootAssembly.Set(name='centerSlab', nodes=
#     M.rootAssembly.instances['SLAB-1'].nodes[24:25])
# M.HistoryOutputRequest(createStepName=stepName, name='U2', 
# 	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))


#Change frequency of output for all steps
func.changeFieldOutputFreq(modelName,
	quasiStatic=qsFieldIntervals, colRmv=rmvFieldIntervals,
	free = freeFieldIntervals)
func.changeHistoryOutputFreq(modelName,
	quasiStatic=qsIntervals, colRmv=rmvIntervals,
	free = freeIntervals)



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
	shell.xyUcolTop(modelName, column=APMcol)
	
	# #Force and displacement
	# shell.xyCenterU2_colBaseR2(modelName,x,z)
	
	print '   done'








print '###########    END OF SCRIPT    ###########'

