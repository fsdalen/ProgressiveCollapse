from abaqus import *
from abaqusConstants import *
#====================================================================#
#====================================================================#
#							INPUTS									 #
#====================================================================#
#====================================================================#



run = 		1	     	#If 1: run job
saveModel = 0			#If 1: Save model
cpus = 		1			#Number of CPU's
post = 		1			#Run post prossesing
snurre = 	0			#1 if running on snurre (removes extra commands like display ODB)

modelName = "staticMod"
jobName = 'staticJob'
stepName = "staticStep"	

#4x4  x10(5)
x = 2			#Nr of columns in x direction
z = 2			#Nr of columns in z direction
y = 1			#nr of stories


#================ Step ==================#
static = 1					# 1 if static
riks =   0					# 1 if Riks static
nlg = OFF					# Nonlinear geometry (ON/OFF)

inInc = 1e-5				# Initial increment
minIncr = 1e-9
histIntervals = 10 			#History output evenly spaced over n increments

#================ Post =============#
#Plots
plotVonMises = 1
plotPEEQ = 1
U2rmvCol = 0

#Other
defScale = 10
printFormat = PNG #TIFF, PS, EPS, PNG, SVG

#================ Materials ==================#
# Material 1
matFile = 'mat_1.inp'
mat1 = "DOMEX_S355"		#Material name

# Material 2
mat2 = "Concrete"	#Material name
mat2_Description = 'This is the description'
mat2_dens = 2.5e-09		#Density
mat2_E = 35000.0		#E-module
mat2_v = 0.3			#Poisson
mat2_yield = 355.0			#Yield stress

# Material 3
mat3 = "Rebar Steel"		#Material name
mat3_Description = 'This is the description'
mat3_dens = 8.0e-09		#Density
mat3_E = 210000.0		#E-module
mat3_v = 0.3			#Poisson
mat3_yield = 355.0		#Yield stress


#================ Parts ==================#
#Column
part1 = "COLUMN"
sect1 = "HUP"
col1_height = 4000.0
imp = 0				#Initial imperfection ("triangle" shape)

#Beam
part2 = "BEAM"
sect2 = "HEB"
beam_len = 8000.0

#Slab
part3 = "SLAB"
sect3 = "Slab"
deck_t = 200.0	#Thickness of slabs

#Rebars in Slab
rebarDim = 20.0			#mm^2 diameter
rebarArea = 3.1415*(rebarDim/2.0)**2		#mm^2
rebarSpacing = 120.0		#mm
rebarPosition = -80.0		#mm distance from center of section


#================ Assembly ==================#
x_d = beam_len		#Size of bays in x direction
z_d = beam_len		#Size of bays in z direction

dep = ON		#Dependent (ON) or independent (OFF) instances

#================ Mesh ==================#
analysisType = STANDARD  #Could be STANDARD or EXPLICIT

#Column
seed1 = 800.0
element1 = B31 #B31 or B32 for linear or quadratic

#Beam
seed2 = seed1
element2 = element1 #B31 or B32 for linear or quadratic

#Slab
seed3 = seed1
element3 = S4R #S4R or S8R for linear or quadratic (S8R is not available for Explicit)



#================ Loads ==================#
LL_kN_m = -2.0	    #kN/m^2

LL=LL_kN_m * 1.0e-3   #N/mm^2




#====================================================================#
#						PRELIMINARIES								 #
#====================================================================#
print '\n'*6
print '###########    NEW SCRIPT    ###########'

from datetime import datetime
print str(datetime.now())[:19]

from part import *
from material import *
from section import *
from optimization import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *


from abaqus import *			#These statements make the basic Abaqus objects accessible to the script... 
from abaqusConstants import *	#... as well as all the Symbolic Constants defined in the Abaqus Scripting Interface.
import odbAccess        		# To make ODB-commands available to the script

#Print status to console during analysis
import simpleMonitor
if not snurre:
	simpleMonitor.printStatus(ON)



#This makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,recoverGeometry=COORDINATE)

#Import model from mat input file
print '\n'*2
mdb.ModelFromInputFile(name=modelName, inputFileName=matFile)
print '\n'*2

		
M = mdb.models[modelName]

#Deletes all other models
if len(mdb.models.keys()) > 0:							
	a = mdb.models.items()
	for i in range(len(a)):
		b = a[i]
		if b[0] != modelName:
			del mdb.models[b[0]]


			
#================ Close and delete old jobs and ODBs ==================#
# This is in order to avoid corrupted files because when running in Parallels

if 1:
	#Close and delete odb files
	import os
	import glob
	fls = glob.glob('*.odb')
	for i in fls:
		if len(session.odbs.keys())>0:
			session.odbs[i].close()
		os.remove(i)
	#Delete old input files
	inpt = glob.glob('*.inp')
	for i in inpt:
		if not i == matFile:
			os.remove(i)
	#Delete old jobs
	jbs = mdb.jobs.keys()
	if len(jbs)> 0:
		for i in jbs:
			del mdb.jobs[i]
	print 'Old jobs and ODBs have been closed.'




#====================================================================#
#						MATERIALS 									 #
#====================================================================#



#================ Steel ==================#
# mat1_Description = 'This is the description'
# mat1_dens = 8.0e-09		#Density
# mat1_E = 210000.0		#E-module
# mat1_v = 0.3			#Poisson
# mat1_yield = 355.0		#Yield stress
# 
# M.Material(description=mat1_Description, name=mat1)
# M.materials[mat1].Density(table=((mat1_dens, ), ))
# M.materials[mat1].Elastic(table=((mat1_E, mat1_v), ))
# M.materials[mat1].Plastic(table=((mat1_yield, 0.0), ))

# #Hardning (random linear interpolatin)
# M.materials[mat1].plastic.setValues(table=((355.0, 
    # 0.0), (2000.0, 20.0)))

#Damping (almost random mass proportional damping)
M.materials[mat1].Damping(beta=0.0031)

#================ Concrete ==================#
M.Material(description=mat2_Description, name=mat2)
M.materials[mat2].Density(table=((mat2_dens, ), ))
M.materials[mat2].Elastic(table=((mat2_E, mat2_v), ))
M.materials[mat2].Plastic(table=((mat2_yield, 0.0), ))

#Damping (almost random mass proportional damping)
M.materials[mat2].Damping(beta=0.0031)

#================ Rebar Steel ==================#
M.Material(description=mat3_Description, name=mat3)
M.materials[mat3].Density(table=((mat3_dens, ), ))
M.materials[mat3].Elastic(table=((mat3_E, mat3_v), ))
M.materials[mat3].Plastic(table=((mat3_yield, 0.0), ))

#Hardning (random linear interpolatin)
M.materials[mat3].plastic.setValues(table=((355.0, 
    0.0), (2000.0, 20.0)))

#Damping (almost random mass proportional damping)
M.materials[mat3].Damping(beta=0.0031)



#====================================================================#
#						PARTS	 									 #
#====================================================================#

#================ Column ==================#
#Create Section and profile
#RHS 300x300
M.BoxProfile(a=300.0, b=300.0, name='Profile-1', t1=10.0, uniformThickness=ON)
M.BeamSection(consistentMassMatrix=False, integration=
    DURING_ANALYSIS, material=mat1, name=sect1, poissonRatio=0.3, 
    profile='Profile-1', temperatureVar=LINEAR)

if imp >0:
	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize=20.0)
	M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(imp, col1_height/2.0))
	M.sketches['__profile__'].Line(point1=(imp, col1_height/2.0), point2=(0.0, col1_height))
	M.Part(dimensionality=THREE_D, name=part1, type=DEFORMABLE_BODY)
	M.parts[part1].BaseWire(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']
else:
	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize=20.0)
	M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(0.0, col1_height))
	M.Part(dimensionality=THREE_D, name=part1, type=DEFORMABLE_BODY)
	M.parts[part1].BaseWire(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']


#Assign section
M.parts[part1].SectionAssignment(offset=0.0, 
    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
    edges=M.parts[part1].edges.findAt(((0.0, 0.0, 
    0.0), ), )), sectionName=sect1, thicknessAssignment=FROM_SECTION)

if imp >0.0:
	M.parts[part1].SectionAssignment(offset=0.0, 
		offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
		edges=M.parts[part1].edges.findAt(((0.0, col1_height, 
		0.0), ), )), sectionName=sect1, thicknessAssignment=FROM_SECTION)


#Assign beam orientation
M.parts[part1].assignBeamSectionOrientation(method=
    N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
    edges=M.parts[part1].edges.findAt(((0.0, 0.0, 0.0), ), )))

if imp >0:
	M.parts[part1].assignBeamSectionOrientation(method=
		N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
		edges=M.parts[part1].edges.findAt(((0.0, col1_height, 0.0), ), )))



# Create sets of column base/top
# Will get name "part1_an-e.col-base" in assembly
M.parts[part1].Set(name='col-base', vertices=
    M.parts[part1].vertices.findAt(((0.0, 0.0, 0.0),)))		
M.parts[part1].Set(name='col-top', vertices=
    M.parts[part1].vertices.findAt(((0.0, col1_height, 0.0),)))

#Create set of part
M.parts[part1].Set(edges=
    M.parts[part1].edges.findAt(((0.0, 1.0, 0.0), )), 
    name=part1)


#================ Beam ==================#
#Create Section and profile
#HEB 550
M.IProfile(b1=300.0, b2=300.0, h=550.0, l=275.0, name=
    'Profile-2', t1=29.0, t2=29.0, t3=15.0)	#Now IPE profile, see ABAQUS for geometry definitions

M.BeamSection(consistentMassMatrix=False, integration=
    DURING_ANALYSIS, material=mat1, name=sect2, poissonRatio=0.3, 
    profile='Profile-2', temperatureVar=LINEAR)

#Create part
M.ConstrainedSketch(name='__profile__', sheetSize=10000.0)
M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(beam_len, 0.0))
M.Part(dimensionality=THREE_D, name=part2, type=DEFORMABLE_BODY)
M.parts[part2].BaseWire(sketch=M.sketches['__profile__'])
del M.sketches['__profile__']

#Assign section
M.parts[part2].SectionAssignment(offset=0.0, 
    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
    edges=M.parts[part2].edges.findAt(((0.0, 0.0, 
    0.0), ), )), sectionName=sect2, thicknessAssignment=FROM_SECTION)

#Assign beam orientation
M.parts[part2].assignBeamSectionOrientation(method=
    N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
    edges=M.parts[part2].edges.findAt(((0.0, 0.0, 0.0), ), )))

#Create set of part
M.parts[part2].Set(edges=
    M.parts[part2].edges.findAt(((1.0, 0.0, 0.0), )), 
    name=part2)

	
#================ Slab ==================#
#Create Section
M.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
    integrationRule=SIMPSON, material=mat2, name=sect3, numIntPts=5, 
    poissonDefinition=DEFAULT, preIntegrate=OFF, temperature=GRADIENT, 
    thickness=deck_t, thicknessField='', thicknessModulus=None, thicknessType=
    UNIFORM, useDensity=OFF)
	
#Add rebars to section
M.sections[sect3].RebarLayers(layerTable=(
    LayerProperties(barArea=rebarArea, orientationAngle=0.0, barSpacing=rebarSpacing, 
    layerPosition=rebarPosition, layerName='Layer 1', material=mat3), ), 
    rebarSpacing=CONSTANT)	
	
#Create part
M.ConstrainedSketch(name='__profile__', sheetSize= 10000.0)
M.sketches['__profile__'].rectangle(point1=(0.0, 0.0), point2=(beam_len, beam_len))
M.Part(dimensionality=THREE_D, name=part3, type=DEFORMABLE_BODY)
M.parts[part3].BaseShell(sketch=M.sketches['__profile__'])
del M.sketches['__profile__']

#Assign section
M.parts[part3].SectionAssignment(offset=0.0, 
    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
    faces=M.parts[part3].faces.findAt(((0.0, 
    0.0, 0.0), ), )), sectionName='Slab', 
    thicknessAssignment=FROM_SECTION)

	
#Assign Rebar Orientation
M.parts[part3].assignRebarOrientation(
    additionalRotationType=ROTATION_NONE, axis=AXIS_1, fieldName='', localCsys=
    None, orientationType=GLOBAL, region=Region(
    faces=M.parts[part3].faces.findAt(((0.1, 
    0.1, 0.0), (0.0, 0.0, 1.0)), )))

	
#Create surface
#Gets name Slab_A1-1.Surf
M.parts[part3].Surface(name='Surf', side2Faces=
    M.parts[part3].faces.findAt(((0.0, 0.0, 0.0), )))

#Create set of part
M.parts[part3].Set(faces=
    M.parts[part3].faces.findAt(((1.0, 1.0, 0.0), )), 
    name=part3)



#====================================================================#
#						ASSEMBLY 									 #
#====================================================================#

print 'Assembling instances...'
M.rootAssembly.DatumCsysByDefault(CARTESIAN)  #Set coordinates to Cartesian
#Letters go left to right (positive x)
#Number top to bottom (positive z)
alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
numb = map(str,range(1,z+1))
etg = map(str,range(1,y+1))

#Lists of all instances
columnList = []
beamList = []
slabList = []

#================ Columns ==================#
count=-1
for a in alph:
	count = count + 1
	for n in numb:
		for e in etg:
			inst = part1 + "_" + a + n + "-" + e
			columnList.append(inst)
			M.rootAssembly.Instance(dependent=dep,		#import and name instance
				name= inst,
				part=M.parts[part1])
			M.rootAssembly.translate(instanceList=(inst, ),	#Translate instance in x,y and z
				vector=(x_d*count , col1_height*(int(e)-1), z_d*(int(n)-1)))

#================ Beams ==================#
#Beams in x (alpha) direction
for a in range(len(alph)-1):
	for n in range(len(numb)-0):
		for e in range(len(etg)):
			inst = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]		
			beamList.append(inst)
			#import and name instance
			M.rootAssembly.Instance(dependent=dep,name=inst, part=M.parts[part2])
			M.rootAssembly.translate(instanceList=(inst, ),
				vector=(x_d*a , col1_height*(e+1), z_d*n))

#Beams in z (numb) direction
#a=0
for a in [0,x-1]:
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			beamList.append(inst)
			# import and name instance
			M.rootAssembly.Instance(dependent=dep,name=inst, part=M.parts[part2])
			# Rotate instance
			M.rootAssembly.rotate(angle=-90.0, axisDirection=(
				0.0,1.0, 0.0), axisPoint=(0.0, 0.0, 0.0), instanceList=(inst, ))
			# Translate instance in x,y and z
			M.rootAssembly.translate(instanceList=(inst, ),
				vector=(x_d*a , col1_height*(e+1), z_d*n))	


#================ Slabs ==================#
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
			slabList.append(inst)
			M.rootAssembly.Instance(dependent=dep,name=inst, part=M.parts[part3])
			M.rootAssembly.rotate(angle=-90.0, axisDirection=(
				1.0,0.0, 0.0), axisPoint=(0.0, 0.0, 0.0), instanceList=(inst, ))
			M.rootAssembly.translate(instanceList=(inst, ),
				vector=(x_d*a,col1_height*(e+1),z_d*(n+1)))

print '    done'



#====================================================================#
#							Mesh 									 #
#====================================================================#

#================ Column ==================#
#Seed
M.parts[part1].seedPart(minSizeFactor=0.1, size=seed1)

#Change element type
M.parts[part1].setElementType(elemTypes=(ElemType(
	elemCode=element1, elemLibrary=analysisType), ), regions=(
	M.parts[part1].edges.findAt((0.0, 0.0, 0.0), ), ))

#Mesh
M.parts[part1].generateMesh()

#================ Beam ==================#
#Seed
M.parts[part2].seedPart(minSizeFactor=0.1, size=seed2)

#Change element type
M.parts[part2].setElementType(elemTypes=(ElemType(
	elemCode=element2, elemLibrary=analysisType), ), regions=(
	M.parts[part2].edges.findAt((0.0, 0.0, 0.0), ), ))

#Mesh
M.parts[part2].generateMesh()

#================ Slab ==================#
#Seed
M.parts[part3].seedPart(minSizeFactor=0.1, size=seed3)

#Change element type
M.parts[part3].setElementType(elemTypes=(ElemType(
	elemCode=S4R, elemLibrary=analysisType, secondOrderAccuracy=OFF, 
	hourglassControl=DEFAULT), ElemType(elemCode=S3R, elemLibrary=analysisType)), 
	regions=(M.parts[part3].faces.findAt((0.0, 0.0, 0.0), ), ))

#Mesh
M.parts[part3].generateMesh()




#====================================================================#
#							STEP 									 #
#====================================================================#

#================ Create step ==================#
oldStep = 'Initial'
if static:
	M.StaticStep(description='description', 
		initialInc=inInc, minInc=minIncr, name=stepName, nlgeom=nlg, previous=oldStep)
elif riks:
	M.StaticRiksStep(description='description', initialArcInc=inInc,
		name=stepName, nlgeom=nlg, previous=oldStep, maxLPF=1.0, minArcInc=minIncr)


#====================================================================#
#							HISTORY OUTPUT							 #
#====================================================================#		
def createHistoryOptput(histIntervals):
	M.rootAssembly.regenerate()

	#Delete default history output
	del M.historyOutputRequests['H-Output-1']

	#Create deformation history output for top of deleted Column
	if U2rmvCol:
		M.HistoryOutputRequest(name=column+'_top'+'U', 
			createStepName=stepName, variables=('U2',), 
			region=M.rootAssembly.allInstances[column].sets['col-top'], sectionPoints=DEFAULT, 
			rebar=EXCLUDE, numIntervals=histIntervals)

	#Create history output for energies
	M.HistoryOutputRequest(name='Energy', 
		createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'), 
		numIntervals=histIntervals)
	'''
	ALLAE
	'Artificial' strain energy associated with constraints used to remove singular modes
	(such as hourglass control) and with constraints used to make the drill rotation
	follow the in-plane rotation of the shell elements.

	ALLCD
	Energy dissipated by viscoelasticity.

	ALLIE
	Total strain energy. (ALLIE=ALLSE + ALLPD + ALLCD + ALLAE + ALLDMD+ ALLDC+ ALLFC.)

	ALLKE
	Kinetic energy.

	ALLPD
	Energy dissipated by rate-independent and rate-dependent plastic deformation.

	ALLSE
	Recoverable strain energy.

	ALLVD
	Energy dissipated by viscous effects.

	ALLWK
	External work.

	ALLDMD
	Energy dissipated by damage.

	ALLMW
	Work done in propelling mass added in mass scaling. (Available only for the whole model.)

	ETOTAL
	total energy
	'''
	return
		
createHistoryOptput(histIntervals)
		
#====================================================================#
#							Joints 									 #
#====================================================================#
print 'Adding constraints...'


#================ Column to beam joints =============#

beamMPC = TIE_MPC	#May be TIE/BEAM/PIN

# Using MPC constraints to create pinned joints for the entire frame
# Might be possible to use MPC constraints, Beam or Tie to to get a fixed joint


#Column to beam in x(alpha) direction
for a in range(len(alph)-1):
	for n in range(len(numb)):
		for e in range(len(etg)):
			col = part1+"_"+ alph[a]+numb[n] + "-" +etg[e]
			beam = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]
			constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]
			#MPC
			M.MultipointConstraint(controlPoint=Region(
				vertices=M.rootAssembly.instances[col].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )),\
				csys=None, mpcType=beamMPC, \
				name=constrName, \
				surface=Region(vertices=M.rootAssembly.instances[beam].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )), userMode=DOF_MODE_MPC, userType=0)

#Column to beam in negative x(alpha) direction
for a in range(len(alph)-1, 0,-1):
	for n in range(len(numb)):
		for e in range(len(etg)):
			col = part1+"_"+ alph[a]+numb[n] + "-" +etg[e]
			beam = part2+"_"+ alph[a-1]+numb[n] + "-" + alph[a]+numb[n] + "-"+etg[e]
			constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + alph[a-1]+numb[n] + "-"+etg[e]
			#MPC
			M.MultipointConstraint(controlPoint=Region(
				vertices=M.rootAssembly.instances[col].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )),\
				csys=None, mpcType=beamMPC, \
				name=constrName, \
				surface=Region(vertices=M.rootAssembly.instances[beam].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )), userMode=DOF_MODE_MPC, userType=0)

#Column to beam in z(num) direction
for a in [0,x-1]:
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			col = part1+"_"+ alph[a]+numb[n] + "-" +etg[e]
			beam = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			#MPC
			M.MultipointConstraint(controlPoint=Region(
				vertices=M.rootAssembly.instances[col].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )),\
				csys=None, mpcType=beamMPC, \
				name=constrName, \
				surface=Region(vertices=M.rootAssembly.instances[beam].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )), userMode=DOF_MODE_MPC, userType=0)

#Column to beam in negative z(num) direction
for a in [0,x-1]:
	for n in range(len(numb)-1,0,-1):
		for e in range(len(etg)):
			col = part1+"_"+ alph[a]+numb[n] + "-" +etg[e]
			beam = part2+"_"+ alph[a]+numb[n-1] + "-" + alph[a]+numb[n] + "-"+etg[e]
			constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + alph[a]+numb[n-1] + "-"+etg[e]
			#MPC
			M.MultipointConstraint(controlPoint=Region(
				vertices=M.rootAssembly.instances[col].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )),\
				csys=None, mpcType=beamMPC, \
				name=constrName, \
				surface=Region(vertices=M.rootAssembly.instances[beam].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )), userMode=DOF_MODE_MPC, userType=0)


#================ Column to column joints =============#
colMPC = TIE_MPC

for a in range(len(alph)):
	for n in range(len(numb)):
		for e in range(len(etg)-1):
			col = part1+"_"+ alph[a]+numb[n] + "-" +etg[e]
			col2 = part1+"_"+ alph[a]+numb[n] + "-" +etg[e+1]
			constrName = 'Const_col_col_'+ alph[a]+numb[n] + "-"+etg[e] + "-"+etg[e+1]
			#MPC
			M.MultipointConstraint(controlPoint=Region(
				vertices=M.rootAssembly.instances[col].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )),\
				csys=None, mpcType=colMPC, \
				name=constrName, \
				surface=Region(vertices=M.rootAssembly.instances[col2].vertices.findAt(
				((a*x_d, (e+1)*col1_height, n*z_d), ), )), userMode=DOF_MODE_MPC, userType=0)
				

#================ Slabs to beams =============#

#Create beam surfaces in x (alpha) direction
for a in range(len(alph)-1):
	for n in range(len(numb)-0):
		for e in range(len(etg)):
			inst = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]		
			M.rootAssembly.Surface(circumEdges=
				M.rootAssembly.instances[inst].edges.findAt(
				((x_d*a+1 , col1_height*(e+1), z_d*n), ), ), name=inst+'_surf')

#Create beam surfaces in z (numb) direction
for a in [0, x-1]:
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			M.rootAssembly.Surface(circumEdges=
				M.rootAssembly.instances[inst].edges.findAt(
				((x_d*a , col1_height*(e+1), z_d*n+1), ), ), name=inst+'_surf')

#Create slab edge surfaces
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
			M.rootAssembly.Surface(name=inst+'_edges', side1Edges=
				M.rootAssembly.instances[inst].edges.findAt(
				((x_d*a+1, col1_height*(e+1), z_d*n), ),
				((x_d*a+1, col1_height*(e+1), z_d*n+x_d), ),
				#((x_d*a, col1_height*(e+1), z_d*n+1), ),
				#((x_d*a+x_d, col1_height*(e+1), z_d*n+1), ), 
				))

# a=0
# for n in range(len(numb)-1):
	# for e in range(len(etg)):
		# inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
		# M.rootAssembly.Surface(name=inst+'_edges', side1Edges=
			# M.rootAssembly.instances[inst].edges.findAt(
			# ((x_d*a+1, col1_height*(e+1), z_d*n), ),
			# ((x_d*a+1, col1_height*(e+1), z_d*n+x_d), ),
			# ((x_d*a, col1_height*(e+1), z_d*n+1), ),
			# #((x_d*a+x_d, col1_height*(e+1), z_d*n+1), ),
			# ))

# a=x-2
# for n in range(len(numb)-1):
	# for e in range(len(etg)):
		# inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
		# M.rootAssembly.Surface(name=inst+'_edges', side1Edges=
			# M.rootAssembly.instances[inst].edges.findAt(
			# ((x_d*a+1, col1_height*(e+1), z_d*n), ),
			# ((x_d*a+1, col1_height*(e+1), z_d*n+x_d), ),
			# #((x_d*a, col1_height*(e+1), z_d*n+1), ),
			# ((x_d*a+x_d, col1_height*(e+1), z_d*n+1), ),
			# ))
				
				
#Join beam surfaces to match slabs
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
			beam1 = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]
			beam2 = part2+"_"+ alph[a]+numb[n+1] + "-" + alph[a+1]+numb[n+1] + "-"+etg[e]
			#beam3 = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			#beam4 = part2+"_"+ alph[a+1]+numb[n] + "-" + alph[a+1]+numb[n+1] + "-"+etg[e]
			M.rootAssembly.SurfaceByBoolean(name=inst+'_beamEdges', 
				surfaces=(
				M.rootAssembly.surfaces[beam1+'_surf'], 
				M.rootAssembly.surfaces[beam2+'_surf'],
				#M.rootAssembly.surfaces[beam3+'_surf'],
				#M.rootAssembly.surfaces[beam4+'_surf']
				))

# a=0
# for n in range(len(numb)-1):
	# for e in range(len(etg)):
		# inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
		# beam1 = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]
		# beam2 = part2+"_"+ alph[a]+numb[n+1] + "-" + alph[a+1]+numb[n+1] + "-"+etg[e]
		# beam3 = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
		# M.rootAssembly.SurfaceByBoolean(name=inst+'_beamEdges', 
			# surfaces=(
			# M.rootAssembly.surfaces[beam1+'_surf'], 
			# M.rootAssembly.surfaces[beam2+'_surf'],
			# M.rootAssembly.surfaces[beam3+'_surf'],))

# a=x-2
# for n in range(len(numb)-1):
	# for e in range(len(etg)):
		# inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
		# beam1 = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]
		# beam2 = part2+"_"+ alph[a]+numb[n+1] + "-" + alph[a+1]+numb[n+1] + "-"+etg[e]
		# beam4 = part2+"_"+ alph[a+1]+numb[n] + "-" + alph[a+1]+numb[n+1] + "-"+etg[e]
		# M.rootAssembly.SurfaceByBoolean(name=inst+'_beamEdges', 
			# surfaces=(
			# M.rootAssembly.surfaces[beam1+'_surf'], 
			# M.rootAssembly.surfaces[beam2+'_surf'],
			# M.rootAssembly.surfaces[beam4+'_surf'],))


#Tie slabs to beams (beams as master)
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
			M.Tie(adjust=ON, master=
				M.rootAssembly.surfaces[inst+'_beamEdges'],
				name=inst, positionToleranceMethod=COMPUTED, slave=
				M.rootAssembly.surfaces[inst+'_edges']
				, thickness=OFF, tieRotations=OFF)

print '    done'




#====================================================================#
#							BCs 									 #
#====================================================================#

#================ Loads ==================#

# Gravity
M.Gravity(comp2=-9800.0, createStepName=stepName, 
    distributionType=UNIFORM, field='', name='Gravity')

 
# LL
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part3+'_'+ alph[a]+numb[n]+"-"+etg[e]
			M.SurfaceTraction(createStepName=stepName, 
				directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
				distributionType=UNIFORM, field='', follower=OFF,
				localCsys=None, magnitude= LL, name="Slab_" + alph[a]+numb[n]+"-"+etg[e],
				region= M.rootAssembly.instances[inst].surfaces['Surf'],
				traction=GENERAL)



#================ Column base =============#

for a in alph:
	for n in numb:
		set = part1 + "_" + a + n + "-" + "1.col-base"
		M.DisplacementBC(amplitude=UNSET, createStepName=
			'Initial', distributionType=UNIFORM, fieldName='', fixed=OFF,
			localCsys=None, name=set, region=
			M.rootAssembly.sets[set], u1=0.0, u2=0.0, u3=0.0
			, ur1=0.0, ur2=0.0, ur3=0.0)





#====================================================================#
#							JOB 									 #
#====================================================================#
M.rootAssembly.regenerate()

def dispJob():
	if snurre:
		return
	fullJobName = jobName+'.odb'
	fls = glob.glob('*.odb')
	for i in fls:
		if i == fullJobName:
			dispObj = session.openOdb(name=fullJobName)
			session.viewports['Viewport: 1'].setValues(displayedObject=dispObj)
			session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(
				CONTOURS_ON_DEF, ))
			session.viewports['Viewport: 1'].odbDisplay.commonOptions.setValues(
				uniformScaleFactor=10)
		else:
			print 'Error opening ODB, jobName does not exist'
	return
	
if saveModel == 1:
	mdb.saveAs(pathName = modelName + '.cae')

mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model=modelName, modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name=jobName, nodalOutputPrecision=SINGLE, 
    numCpus=cpus, numDomains=cpus, numGPUs=0, queue=None, resultsFormat=ODB, scratch=
    '', type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)


def runJob(jobName):
	print 'Running %s...' %jobName
	try:
		mdb.jobs[jobName].submit(consistencyChecking=OFF)	#Run job
		mdb.jobs[jobName].waitForCompletion()
		dispJob()
	except:
		print mdb.jobs[jobName].status

if run:    
	runJob(jobName)


#====================================================================#
#							POST PROCESSING							 #
#====================================================================#

#============ XY plot print function ============#
def XYprint(odbName, plotName,printFormat, *args):
	V=session.viewports['Viewport: 1']
	#Open ODB
	odb = odbFunc.open_odb(odbName)
	#Turn on background and compass for printing
	session.printOptions.setValues(vpBackground=ON, compass=ON)
	#Create plot
	if plotName not in session.xyPlots.keys():
		session.XYPlot(plotName)
	#Set some variables
	xyp = session.xyPlots[plotName]
	chartName = xyp.charts.keys()[0]
	chart = xyp.charts[chartName]
	#Create plot
	chart.setValues(curvesToPlot=args)
	#Show plot
	V.setValues(displayedObject=xyp)
	#Print plot
	session.printToFile(fileName='plot_XY_'+plotName, format=printFormat, canvasObjects=(V, ))
	return



if post:
	print 'Post processing...'
	
	#Open ODB
	odb = odbFunc.open_odb(jobName)
	#Clear plots
	for plot in session.xyPlots.keys():
		del session.xyPlots[plot]
		
	
	#================ Contour plots =============#
	#Viewport with countour plot
	V=session.viewports['Viewport: 1']
	V.setValues(displayedObject=odb)
	V.odbDisplay.display.setValues(plotState=(
		CONTOURS_ON_DEF, ))
	V.odbDisplay.commonOptions.setValues(
				deformationScaling=UNIFORM, uniformScaleFactor=defScale)

	#Print plots at the last frame in each step
	for steps in odb.steps.keys():
		V.odbDisplay.setFrame(step=steps, frame=-1)
		if plotVonMises:
			V.odbDisplay.setPrimaryVariable(
				variableLabel='S', outputPosition=INTEGRATION_POINT, refinement=(INVARIANT, 
				'Mises'), )
			session.printToFile(fileName='plot_cont_'+steps+'VonMises', format=printFormat, canvasObjects=(V, ))
		if plotPEEQ:
			V.odbDisplay.setPrimaryVariable(
				variableLabel='PEEQ', outputPosition=INTEGRATION_POINT, )
			session.printToFile(fileName='plot_cont_'+steps+'PEEQ', format=printFormat, canvasObjects=(V, ))
	
	
	#============ XY Energy ============#
	plotName = 'Energy'
	#Create curves to plot
	xy1 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='External work: ALLWK for Whole Model', 
		suppressQuery=True)
	c1 = session.Curve(xyData=xy1)
	xy2 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='Internal energy: ALLIE for Whole Model', 
		suppressQuery=True)
	c2 = session.Curve(xyData=xy2)
	xy3 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='Kinetic energy: ALLKE for Whole Model', 
		suppressQuery=True)
	c3 = session.Curve(xyData=xy3)
	#Plot and Print
	XYprint(jobName, plotName, printFormat, c1, c2, c3)
	
	
	#================ Print XY plot of U2 at top of removed column =============#
	if U2rmvCol:
		plotName = 'U2rmvCol'
		#Find correct historyOutput
		for key in odb.steps[stepName].historyRegions.keys():
			if key.find('Node '+column) > -1:
				histName = key
		histOpt = odb.steps[stepName].historyRegions[histName].historyOutputs
		#Get node number
		nodeNr = histName[-1]
		#Create XY-curve
		xy1 = xyPlot.XYDataFromHistory(odb=odb, 
			outputVariableName=
			'Spatial displacement: U2 PI: '+column+' Node '+nodeNr+' in NSET COL-TOP', 
			suppressQuery=True)
		c1 = session.Curve(xyData=xy1)
		#Plot and Print
		XYprint(jobName, plotName, printFormat, c1)
	
	print '   done'



print '###########    END OF SCRIPT    ###########'

