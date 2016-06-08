#Abaqus modules
from abaqus import *
from abaqusConstants import *
from mesh import *

#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


modelName            = 'apShellImp'
cpus                 = 1			#Number of CPU's

run                  = 1





#=========== Geometry  ============#
#Size 	4x4  x10(5)
x                    = 4			#Nr of columns in x direction
z                    = 4			#Nr of columns in z direction
y                    = 5			#nr of stories



#=========== Static step  ============#
static_Type    = 'general' 	#'general' or 'riks'
static_InInc   = 0.1		# Initial increment
static_MinIncr = 1e-9		# Smalles allowed increment
static_maxInc  = 50 		# Maximum number of increments 


#=========== Implicit step  ============#
#Single APM
APMcol        = 'D4-1'

rmvStepTime   = 20e-3		
dynStepTime   = 2.0

dynamic_InInc = 0.1
dynamic_MaxInc= 500





#=========== General  ============#
monitor               = 1			#Write status of job continusly in Abaqus CAE

#Live load
LL_kN_m              = -0.5	        #kN/m^2 (-2.0)

#Mesh
seed                 = 150		    #Global seed
slabSeed     		 = 750			#Change seed of slab
steelMatFile   = 'mat_15.inp'  #Damage parameter is a function of element size

#Post
defScale             = 1.0
printFormat          = PNG 		     #TIFF, PS, EPS, PNG, SVG
animeFrameRate       = 40



#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.shell as shell
reload(func)
reload(shell)


mdbName = 'apShellImp'


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

#Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
	distributionType=UNIFORM, field='', name='Gravity',
	amplitude = UNSET)

#LL
LL=LL_kN_m * 1.0e-3   #N/mm^2
shell.surfaceTraction(modelName,stepName, x, z, y, load=LL, amp=UNSET)




#=========== Coulumn removal step  ============#
# Create step for column removal
oldStep = stepName
stepName = 'elmRemStep'
M.ImplicitDynamicsStep( name=stepName,  previous=oldStep, 
	initialInc=rmvStepTime, maxNumInc=50,
	timeIncrementationMethod=FIXED, timePeriod=rmvStepTime,
	nlgeom=ON)

#Remove column
shell.rmvCol(modelName, stepName, column=APMcol)



#=========== Dynamic step  ============#
#Create dynamic APM step
oldStep = stepName
stepName = 'dynamicStep'
M.ImplicitDynamicsStep(initialInc=dynamic_InInc, minInc=5e-07, name=
	stepName, previous=oldStep, timePeriod=dynStepTime, nlgeom=ON,
	maxNumInc=dynamic_MaxInc)


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
M.FieldOutputRequest(name='U', createStepName='static', 
    variables=('U', ))

# #Status field output
# M.FieldOutputRequest(name='Status', createStepName='quasiStatic', 
#     variables=('STATUS', ))


#History output: energy
M.HistoryOutputRequest(name='Energy', 
	createStepName='static', variables=('ALLIE', 'ALLKE'),)

#R2 history at colBases
M.HistoryOutputRequest(createStepName='static', name='R2',
	region=M.rootAssembly.allInstances['FRAME-1'].sets['colBot'],
    variables=('RF2', ))
shell.histColTopU(modelName, stepName='static', column=APMcol       )


# #U2 at slab center (A1-1 slab)
# M.rootAssembly.Set(name='centerSlab', nodes=
#     M.rootAssembly.instances['SLAB-1'].nodes[24:25])
# M.HistoryOutputRequest(createStepName=stepName, name='U2', 
# 	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))



#===========================================================#
#===========================================================#
#                   Save and run                            #
#===========================================================#
#===========================================================#
M.rootAssembly.regenerate()

#Create job
mdb.Job(model=modelName, name=modelName, numCpus=cpus, numDomains=cpus)

#Run job
if run:
	#Save model
	mdb.saveAs(pathName = mdbName + '.cae')
	#Run model
	func.runJob(modelName)
	#Write CPU time to file
	func.readMsgFile(modelName, 'results.txt')



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


	shell.xyUcolTop(modelName, column=APMcol)
	
	# #Force and displacement
	# shell.xyCenterU2_colBaseR2(modelName,x,z)
	
	print '   done'








print '###########    END OF SCRIPT    ###########'

