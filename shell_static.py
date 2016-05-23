#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'shellStatic'
cpus           = 1			#Number of CPU's
monitor        = 1
run            = 1


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 2			#Nr of columns in x direction
z              = 2			#Nr of columns in z direction
y              = 1			#nr of stories


#=========== Static analysis  ============#
static_Type    = 'general' 	#'general' or 'riks'
static_InInc   = 0.1		# Initial increment
static_MinIncr = 1e-9
static_maxInc  = 50 		#Maximum number of increments for static step


#=========== General  ============#
#Live load
LL_kN_m        = -2.0	    #kN/m^2 (-2.0)

#Mesh
seed           = 150.0		#Global seed
slabSeedFactor = 8			#Factor to scale slab seed

#Post
defScale       = 1.0
printFormat    = PNG 		#TIFF, PS, EPS, PNG, SVG
animeFrameRate = 5



#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#

import lib.func as func
import lib.shell as shell
reload(func)
reload(shell)

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

shell.createShellmod(modelName, x, z, y, seed, slabSeedFactor)




#================================================================#
#================================================================#
#                   STEP DEPENDENCIES                            #
#================================================================#
#================================================================#


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
shell.surfaceTraction(modelName,stepName, x, z, y, load=LL)


M.rootAssembly.regenerate()


#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

#Damage field output
M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'),)


#Delete default history output
del M.historyOutputRequests['H-Output-1']

M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),)

#R2 history at colBases
M.HistoryOutputRequest(createStepName=stepName, name='R2',
	region=M.rootAssembly.allInstances['FRAME-1'].sets['colBot'],
    variables=('RF2', ))

#U2 at shell center
M.rootAssembly.Set(name='centerSlab', nodes=
    M.rootAssembly.instances['SLAB-1'].nodes[24:25])
M.HistoryOutputRequest(createStepName=stepName, name='U2', 
	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))



#===========================================================#
#===========================================================#
#                   Save and run                            #
#===========================================================#
#===========================================================#
M.rootAssembly.regenerate()

#Save model
mdb.saveAs(pathName = mdbName + '.cae')

#Create job
mdb.Job(model=modelName, name=modelName, numCpus=cpus)

#Run job
if run:
	func.runJob(modelName)
	#Write CPU time to file
	func.readMsgFile(modelName, 'results.txt')



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


	#R2 at column base
	shell.xyR2colBase(modelName, x,z, printFormat)
	
	#Energy
	func.xyEnergyPrint(modelName, printFormat)

	#U2 at center slab
	plotName='U2centerSlab'
	odb=func.open_odb(modelName)
	xy1 = xyPlot.XYDataFromHistory(odb=odb, outputVariableName=
		'Spatial displacement: U2 PI: SLAB-1 Node 25 in NSET CENTERSLAB', )
	c1 = session.Curve(xyData=xy1)
	func.XYprint(modelName, plotName, printFormat, c1)
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy1, ))
	func.fixReportFile(tempFile, plotName, modelName,
		xVar='Displacement [mm]', yVar ='Time [s]')
	
	print '   done'


print '###########    END OF SCRIPT    ###########'