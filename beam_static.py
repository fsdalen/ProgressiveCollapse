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
monitor        = 1

run            = 1


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 2			#Nr of columns in x direction
z              = 2			#Nr of columns in z direction
y              = 1			#nr of stories


#=========== Static analysis  ============#
static_Type    = 'riks' 	#'general' or 'riks'
static_InInc   = 0.1		# Initial increment
static_MinIncr = 1e-9
static_maxInc  = 50 		#Maximum number of increments for static step


#=========== General  ============#
#Live load
LL_kN_m        = -2.0	    #kN/m^2 (-2.0)

#Mesh
seed           = 750.0		#Global seed
slabSeedFactor = 1			#Change seed of slab

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

#Damage field output
M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'))

#Delete default history output
del M.historyOutputRequests['H-Output-1']

#Energies
M.HistoryOutputRequest(name='Energy', 
	createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),)

#R2 at all col-bases
M.HistoryOutputRequest(createStepName='static', name='R2',
	region=M.rootAssembly.sets['col-bases'], variables=('RF2', ))

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
mdb.Job(model=modelName, name=modelName, numCpus=cpus)

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

	#Open ODB
	odb = func.open_odb(modelName)
	#Clear xy plots and data
	#func.clearXY()


	# #=========== Contour  ============#
	# func.countourPrint(modelName, defScale, printFormat)

	# #=========== Animation  ============#
	# func.animate(modelName, defScale, frameRate= animeFrameRate)


	#=========== Energy  ============#
	func.xyEnergyPlot(modelName)


	#=========== R2 at column base  ============#
	#Create xy data for each col base
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	count = 0
	lst=[]
	for a in alph:
		for n in numb:
			count = count + 1
			inst = 'COLUMN_' + a + n + "-1"
			name='Reaction force: RF2 PI: '+inst+' Node 1'
			lst.append(xyPlot.XYDataFromHistory(odb=odb,
				outputVariableName=name))
	tpl=tuple(lst)
	#Compine all to one xyData
	xyR2 = sum(tpl)
	#Plot
	func.XYplot(modelName,
		plotName='R2colBase',
		xHead='Time [s]', yHead='Force [N]',
		xyDat=xyR2)
	
	
	#=========== U2 at center slab  ============#
	odb=func.open_odb(modelName)
	xyU2 = xyPlot.XYDataFromHistory(odb=odb, outputVariableName=
    	'Spatial displacement: U2 PI: SLAB_A1-1 Node 61 in NSET CENTERSLAB',
    	name='xyU2')
	func.XYplot(modelName,
		plotName='U2centerSlab',
		xHead='Time [s]', yHead='Displacement [mm]',
		xyDat=xyU2)


	#=========== Force-Displacement  ============#
	xyRD = combine(-xyU2,xyR2)
	func.XYplot(modelName,
		plotName='forceDisp',
		xHead='Displacement [mm]', yHead='Force [N]', 
		xyDat=xyRD)	
	

	print '   done'


print '###########    END OF SCRIPT    ###########'
