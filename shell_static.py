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
run            = 0


#=========== Geometry  ============#
#Size 	4x4  x10(5)
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
LL_kN_m        = -2.0	    #kN/m^2 (-2.0)

#Mesh
seed           = 150.0		#Global seed

#Post
defScale       = 1.0
printFormat    = PNG 		#TIFF, PS, EPS, PNG, SVG
fieldIntervals = 30
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
rebarSteel = 'Rebar Steel'

#Set up model with materials
func.perliminary(monitor, modelName, steel, concrete, rebarSteel)

M=mdb.models[modelName]




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#Build geometry

shell.createShellmod(modelName, x, z, y, steel, concrete, rebarSteel, seed)




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

M.SurfaceTraction(createStepName=stepName, 
	directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
	distributionType=UNIFORM, field='', follower=OFF,
	localCsys=None, magnitude= LL,
	name="LL",
	region=M.rootAssembly.instances['Part-1-1'].surfaces['topSurf'],
	traction=GENERAL)

M.rootAssembly.regenerate()


#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#


#Delete default history output
del M.historyOutputRequests['H-Output-1']



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

	#=========== Contour  ============#
	func.countourPrint(modelName, defScale, printFormat)

	#=========== Animation  ============#
	func.animate(modelName, defScale, frameRate= animeFrameRate)
	
	print '   done'


print '###########    END OF SCRIPT    ###########'