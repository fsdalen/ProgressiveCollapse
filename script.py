#====================================================================#
#						PRELIMINARIES								 #
#====================================================================#


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


#This makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,recoverGeometry=COORDINATE)

modelName = "basicFrame"
mdb.Model(modelType=STANDARD_EXPLICIT, name=modelName) 	#Create a new model 
M = mdb.models[modelName]								#For simplicity
if len(mdb.models.keys()) > 0:							#Deletes all other models
	a = mdb.models.items()
	for i in range(len(a)):
		b = a[i]
		if b[0] != modelName:
			del mdb.models[b[0]]


#================ Close and delete stuff ==================#
# This is in order to avoid corrupted files because when running in Parallels

#Close and delete odb files
import os
import glob
fls = glob.glob('*.odb')
for i in fls:
	session.odbs[i].close()
	os.remove(i)



#Delete old input
inpt = glob.glob('*.inp')
for i in inpt:
	os.remove(i)


#Delete old jobs
jbs = mdb.jobs.keys()
if len(jbs)> 0:
	for i in jbs:
		del mdb.jobs[i]

#====================================================================#
#							INPUTS									 #
#====================================================================#

runJob = 0		     	#If 1: run job
saveModel = 0			#If 1: Save model
cpus = 2				#Number of CPU's


#================ Materials ==================#
# Material 1
mat1 = "Steel"		#Material name
mat1_Description = 'This is the description'
mat1_dens = 8.05e-09	#Density
mat1_E = 210000.0		#E-module
mat1_v = 0.3			#Poisson
mat1_yield = 355		#Yield stress

# Material 2
mat2 = "Concrete"	#Material name
mat2_Description = 'This is the description'
mat2_dens = 2.5e-09		#Density
mat2_E = 35000.0		#E-module
mat2_v = 0.3			#Poisson
mat2_yield = 35			#Yield stress


#================ Parts ==================#
#Column
part1 = "Column"
sect1 = "HUP"
col1_height = 500

#Beam
part2 = "Beam"
sect2 = "HUP2"
beam_len = 500

#Slab
part3 = "Slab"
sect3 = "Slab"
deck_t = 10	#Thickness of slabs


#================ Assembly ==================#
x = 2			#Nr of columns in x direction
z = 2			#Nr of columns in z direction
y = 1			#nr of stories
x_d = beam_len		#Size of bays in x direction
z_d = beam_len		#Size of bays in z direction


#================ Mesh ==================#
analysisType = STANDARD  #Could be STANDARD or EXPLICIT

#Column
seed1 = 50
element1 = B31 #B31 or B32 for linear or quadratic

#Beam
seed2 = seed1
element2 = element1 #B31 or B32 for linear or quadratic

#Slab
seed3 = seed1
element3 = S4R #S4R or S8R for linear or quadratic (S8R is not available for Explicit)


#================ Step ==================#
stepName = "Static"			#Name of step

static = 0					# 1 if static
riks = 1					# 1 if Riks static
nlg = ON					# Nonlinear geometry (ON/OFF)


#================ Loads ==================#
LL=-1




#====================================================================#
#						MATERIALS 									 #
#====================================================================#

#================ Steel ==================#
M.Material(description=mat1_Description, name=mat1)
M.materials[mat1].Density(table=((mat1_dens, ), ))
M.materials[mat1].Elastic(table=((mat1_E, mat1_v), ))
M.materials[mat1].Plastic(table=((mat1_yield, 0.0), ))

#================ Concrete ==================#
M.Material(description=mat2_Description, name=mat2)
M.materials[mat2].Density(table=((mat2_dens, ), ))
M.materials[mat2].Elastic(table=((mat2_E, mat2_v), ))
M.materials[mat2].Plastic(table=((mat2_yield, 0.0), ))




#====================================================================#
#						PARTS	 									 #
#====================================================================#

#================ Column ==================#
#Create Section and profile
M.BoxProfile(a=100.0, b=100.0, name='Profile-1', t1=10.0, uniformThickness=ON)
M.BeamSection(consistentMassMatrix=False, integration=
    DURING_ANALYSIS, material='Steel', name=sect1, poissonRatio=0.3, 
    profile='Profile-1', temperatureVar=LINEAR)

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

#Assign beam orientation
M.parts[part1].assignBeamSectionOrientation(method=
    N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
    edges=M.parts[part1].edges.findAt(((0.0, 0.0, 0.0), ), )))


# Create sets of column base/top
# Will get name "part1_an-e.col-base" in assembly
M.parts[part1].Set(name='col-base', vertices=
    M.parts[part1].vertices.findAt(((0.0, 0.0, 0.0),)))		
M.parts[part1].Set(name='col-top', vertices=
    M.parts[part1].vertices.findAt(((0.0, col1_height, 0.0),)))


#================ Beam ==================#
#Create Section and profile
M.IProfile(b1=50.0, b2=50.0, h=100.0, l=50.0, name=
    'Profile-2', t1=5.0, t2=5.0, t3=5.0)	#Now IPE profile, see ABAQUS for geometry definitions

M.BeamSection(consistentMassMatrix=False, integration=
    DURING_ANALYSIS, material='Steel', name=sect2, poissonRatio=0.3, 
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


#================ Slab ==================#
#Create Section
M.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
    integrationRule=SIMPSON, material=mat2, name=sect3, numIntPts=5, 
    poissonDefinition=DEFAULT, preIntegrate=OFF, temperature=GRADIENT, 
    thickness=deck_t, thicknessField='', thicknessModulus=None, thicknessType=
    UNIFORM, useDensity=OFF)

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

#Create surface
#Gets name Slab_A1-1.Surf
M.parts[part3].Surface(name='Surf', side2Faces=
    M.parts[part3].faces.findAt(((0.0, 0.0, 0.0), )))




#====================================================================#
#						ASSEMBLY 									 #
#====================================================================#

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
			M.rootAssembly.Instance(dependent=ON,		#import and name instance
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
			M.rootAssembly.Instance(dependent=ON,name=inst, part=M.parts[part2])
			M.rootAssembly.translate(instanceList=(inst, ),
				vector=(x_d*a , col1_height*(e+1), z_d*n))

#Beams in z (numb) direction
for a in range(len(alph)-0):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			beamList.append(inst)
			#import and name instance
			M.rootAssembly.Instance(dependent=ON,name=inst, part=M.parts[part2])
			#Rotate instance
			M.rootAssembly.rotate(angle=-90.0, axisDirection=(
				0.0,1.0, 0.0), axisPoint=(0.0, 0.0, 0.0), instanceList=(inst, ))
			#Translate instance in x,y and z
			M.rootAssembly.translate(instanceList=(inst, ),
				vector=(x_d*a , col1_height*(e+1), z_d*n))


#================ Slabs ==================#
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
			slabList.append(inst)
			M.rootAssembly.Instance(dependent=ON,name=inst, part=M.parts[part3])
			M.rootAssembly.rotate(angle=90.0, axisDirection=(
							1.0,0.0, 0.0), axisPoint=(0.0, 0.0, 0.0), instanceList=(inst, ))
			M.rootAssembly.translate(instanceList=(inst, ),
							vector=(x_d*a,col1_height*(e+1),z_d*n))




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
if static:
	M.StaticStep(description='description', 
		initialInc=0.1, name=stepName, nlgeom=nlg, previous='Initial')
elif riks:
	M.StaticRiksStep(description='description', 
		initialArcInc=0.01, name=stepName, nlgeom=nlg, previous='Initial')




#====================================================================#
#							Joints 									 #
#====================================================================#

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
for a in range(len(alph)):
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
for a in range(len(alph)):
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
for a in range(len(alph)-0):
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
				((x_d*a, col1_height*(e+1), z_d*n+1), ),
				((x_d*a+x_d, col1_height*(e+1), z_d*n+1), ), ))

#Join beam surfaces to match slabs
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part3+"_"+ alph[a]+numb[n] + "-"+etg[e]
			beam1 = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]
			beam2 = part2+"_"+ alph[a]+numb[n+1] + "-" + alph[a+1]+numb[n+1] + "-"+etg[e]
			beam3 = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			beam4 = part2+"_"+ alph[a+1]+numb[n] + "-" + alph[a+1]+numb[n+1] + "-"+etg[e]
			M.rootAssembly.SurfaceByBoolean(name=inst+'_beamEdges', 
				surfaces=(
				M.rootAssembly.surfaces[beam1+'_surf'], 
				M.rootAssembly.surfaces[beam2+'_surf'],
				M.rootAssembly.surfaces[beam3+'_surf'],
				M.rootAssembly.surfaces[beam4+'_surf']))

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




#====================================================================#
#							BCs 									 #
#====================================================================#

#================ Loads ==================#

#Gravity
# M.Gravity(comp2=-9800.0, createStepName=stepName, 
#     distributionType=UNIFORM, field='', name='Gravity')

 
#LL
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = "Slab_" + alph[a]+numb[n]+"-"+etg[e]
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
			Initial, distributionType=UNIFORM, fieldName='', fixed=OFF,
			localCsys=None, name=set, region=
			M.rootAssembly.sets[set], u1=0.0, u2=0.0, u3=0.0
			, ur1=0.0, ur2=0.0, ur3=0.0)



#====================================================================#
#							JOB 									 #
#====================================================================#
M.rootAssembly.regenerate()

if saveModel == 1:
	mdb.saveAs(pathName = modelName + '.cae')

mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model=modelName, modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name='Job-1', nodalOutputPrecision=SINGLE, 
    numCpus=cpus, numDomains=2, numGPUs=0, queue=None, resultsFormat=ODB, scratch=
    '', type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)

if runJob == 1:        
	mdb.jobs[jobName].submit(consistencyChecking=OFF)	#Run job


