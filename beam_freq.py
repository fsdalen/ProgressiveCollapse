#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'beamFreq'
cpus           = 1			#Number of CPU's
monitor        = 1

run            = 0


#=========== Geometry  ============#
#Size 	4x4  x10(5)
x              = 2			#Nr of columns in x direction
z              = 2			#Nr of columns in z direction
y              = 1			#nr of stories





#=========== General  ============#
#Mesh
seed           = 150.0		#Global seed
slabSeedFactor = 2			#Change seed of slab



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


#Create Frequency step
M.FrequencyStep(name='pertubation', numEigen=10, previous=
    'Initial')
M.rootAssembly.regenerate()



#===========================================================#
#===========================================================#
#                   SAVE AND RUN                            #
#===========================================================#
#===========================================================#

#Create job
mdb.Job(model=modelName, name=modelName, numCpus=cpus)

#Run job
if run:
	#Save model
	mdb.saveAs(pathName = mdbName + '.cae')
	func.runJob(modelName)



print '###########    END OF SCRIPT    ###########'
