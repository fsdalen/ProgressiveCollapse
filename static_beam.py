#Abaqus modules
from abaqus import *
from abaqusConstants import *
import xyPlot


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'beamStatic'
cpus           = 1			#Number of CPU's
monitor        = 0

run            = 0


#=========== Geometry  ============#
#Size 	4x4  x5(10)
x              = 4			#Nr of columns in x direction
z              = 4			#Nr of columns in z direction
y              = 5			#nr of stories


#=========== Static analysis  ============#
static_Type    = 'general' 	#'general' or 'riks'
static_InInc   = 0.1		# Initial increment
static_MinIncr = 1e-9
static_maxInc  = 50 		#Maximum number of increments for static step


#=========== General  ============#
#Live load
LL_kN_m        = -0.5	    #kN/m^2 (-2.0)

#Mesh
seed           = 750.0		#Frame seed
slabSeed       = 750.0 

#Post
defScale       = 1.0
printFormat    = PNG 		#TIFF, PS, EPS, PNG, SVG
animeFrameRate = 5

APMcol        = 'COLUMN_B2-1'		#Column to be removed

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
func.addSlabLoad(M, x, z, y, stepName, LL)



#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#

# #Damage field output
# M.FieldOutputRequest(name='damage', 
#     createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'))

#Delete default history output
del M.historyOutputRequests['H-Output-1']

#Energies
M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE'),)

#R2 at all col-bases
M.HistoryOutputRequest(createStepName='static', name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ))

#U2 at middle (seed750 slabfactor1)
M.rootAssembly.Set(name='centerSlab', nodes=
    M.rootAssembly.instances['SLAB_A1-1'].nodes[60:61])
M.HistoryOutputRequest(createStepName=stepName, name='U2', 
	region=M.rootAssembly.sets['centerSlab'], variables=('U2', ))


#U2 at top of column to later be removed
M.HistoryOutputRequest(name=APMcol+'_top'+'U', 
		createStepName=stepName, variables=('U2',), 
		region=M.rootAssembly.allInstances[APMcol].sets['col-top'])

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

	# #Animation
	# func.animate(modelName, defScale, frameRate= animeFrameRate)

	#Energy
	func.xyEnergyPlot(modelName)

	#R2 at col base
	beam.xyColBaseR2(modelName,x,z)

	#Force and displacement
	beam.xyCenterU2_colBaseR2(modelName,x,z)

	#Displacement at colTop
	beam.xyAPMcolPrint(modelName, APMcol)

	print '   done'


print '###########    END OF SCRIPT    ###########'
