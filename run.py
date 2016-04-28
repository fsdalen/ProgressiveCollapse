





#Size 	4x4  x10(5)
x              = 2			#Nr of columns in x direction
z              = 2			#Nr of columns in z direction
y              = 1			#nr of stories





#=========== Model  ============#
beam           = 1
shell          = 0


#=========== Analysis  ============#
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












#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#




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


