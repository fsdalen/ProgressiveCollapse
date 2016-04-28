#Abaqus modules
from abaqus import *
from abaqusConstants import *


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


mdbName        = 'Static'
cpus           = 1			#Number of CPU's
monitor        = 1


#Size 	4x4  x10(5)
x              = 2			#Nr of columns in x direction
z              = 2			#Nr of columns in z direction
y              = 1			#nr of stories





#=========== Model  ============#
beam           = 1
shell          = 0


#=========== Analysis  ============#
run            = 0	

static         = 1
modelName      = "static"







#=========== Static analysis  ============#
static_Type    = 'general' 	#'general' or 'riks'
static_InInc   = 0.1				# Initial increment
static_MinIncr = 1e-9
static_maxInc  = 50 #Maximum number of increments for static step


#=========== General  ============#
#Live load
LL_kN_m        = -2.0	    #kN/m^2 (-2.0)

#Post
defScale       = 10
printFormat    = PNG 	#TIFF, PS, EPS, PNG, SVG


#============================================================#
#============================================================#
#                   PERLIMINARIES                            #
#============================================================#
#============================================================#



#=========== Import modules  ============#

import os
import glob
from datetime import datetime

import lib.func as func
import lib.beam as beam
reload(func)
reload(beam)


#=========== Other stuff  ============#

#Makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,
	recoverGeometry=COORDINATE)

#Print begin script to console
print '\n'*6
print '###########    NEW SCRIPT    ###########'
print str(datetime.now())[:19]

#Print status to console during analysis
if monitor:
	func.printStatus(ON)

#Create text file to write results in
with open('results.txt', 'w') as f:
	None


#=========== Set up model  ============#
matFile = 'steelMat.inp'

#Create model based on input material
print '\n'*2
mdb.ModelFromInputFile(name=modelName, inputFileName=matFile)
print '\n'*2

#For convinience
M = mdb.models[modelName]

#Deletes all other models
func.delModels(modelName)

#Close and delete old jobs and ODBs
func.delJobs(exeption = matFile)




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#

#=========== Material  ============#
#Material names
steel = 'DOMEX_S355'
concrete = 'Concrete'
rebarSteel = 'Rebar Steel'

func.createMaterials(M, mat1=steel, mat2=concrete, mat3=rebarSteel,)


#=========== Geometry  ============#
if beam:
	beam.buildBeamMod(modelName, x, z, y,
		steel, concrete, rebarSteel)





#===================================================#
#===================================================#
#               STATIC ANALYSIS       		     	#
#===================================================#
#===================================================#


if static:
	func.staticAnalysis(mdbName, modelName, run, static_Type,
	static_InInc, static_MinIncr, static_maxInc, LL_kN_m, defScale,
	printFormat)








print '###########    END OF SCRIPT    ###########'
