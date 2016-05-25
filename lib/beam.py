# Abaqus modules
from abaqus import *
from abaqusConstants import *
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
import odbAccess
import xyPlot
from jobMessage import ANY_JOB, ANY_MESSAGE_TYPE
import animation
import xyPlot

#Python modules
from datetime import datetime
import csv


import func




#===============================================================#
#===============================================================#
#                   Build beam model                            #
#===============================================================#
#===============================================================#


def buildBeamMod(modelName, x, z, y, seed, slabSeedFactor):
	'''
	Builds a beam model without step
	'''

	col_height = 3000.0
	beam_len   = 7500.0

	steel = 'DOMEX_S355'
	concrete = 'Concrete'
	rebarSteel = steel

	M=mdb.models[modelName]

	
	#=========== Parts  ============#
	#Create Column
	createColumn(M, height=col_height, mat=steel, partName='COLUMN')

	#Create Beam
	createBeam(M, length=beam_len, mat=steel, partName='BEAM')

	#Create slab
	createSlab(M, t=200.0, mat=concrete, dim=beam_len,
		rebarMat=rebarSteel, partName='SLAB')

	#Add beam fluid inertia to beams and columns
	airDensity = 1.225e-12    #1.225 kg/m^3
	M.sections['HEB300'].setValues(useFluidInertia=ON,
		fluidMassDensity=airDensity, crossSectionRadius=300.0, 
	    lateralMassCoef=1.0)

	M.sections['HUP300x300'].setValues(useFluidInertia=ON,
		fluidMassDensity=airDensity, crossSectionRadius=300.0, 
	    lateralMassCoef=1.0) 

	#=========== Sets and surfaces  ============#
	#A lot of surfaces are created with the joints
	createSets(M, col_height)
	createSurfs(M)


	#=========== Assembly  ============#
	createAssembly(M, x, z, y,
		x_d = beam_len, z_d = beam_len, y_d = col_height)


	#=========== Mesh  ============#

	mesh(M, seed, slabSeedFactor)

	#Write nr of elements to results file
	M.rootAssembly.regenerate()
	nrElm = elmCounter(M)
	with open('results.txt','a') as f:
		f.write("%s	Elements: %s \n" %(modelName, nrElm))


	#=========== Joints  ============#
	createJoints(M, x, z, y,
		x_d = beam_len, z_d = beam_len, y_d = col_height)


	#=========== Fix column base  ============#
	mergeColBase(M,x,z)
	M.DisplacementBC( createStepName='Initial',
		name='fixColBases', region= M.rootAssembly.sets['col-bases'],
		u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0)






def createColumn(M, height, mat, partName):
	'''
	Creates a RHS 300x300 column

	M: 		model
	height: height of column
	mat:    material
	'''
	
	sectName = "HUP300x300"

	#Create section and profile
	M.BoxProfile(a=300.0, b=300.0, name='Profile-1', t1=10.0, uniformThickness=ON)
	M.BeamSection(consistentMassMatrix=False, integration=
	    DURING_ANALYSIS, material=mat, name=sectName, poissonRatio=0.3, 
	    profile='Profile-1', temperatureVar=LINEAR)

	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize=20.0)
	M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(0.0, height))
	M.Part(dimensionality=THREE_D, name=partName, type=DEFORMABLE_BODY)
	M.parts[partName].BaseWire(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']

	#Assign section
	M.parts[partName].SectionAssignment(offset=0.0, 
	    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 
	    0.0), ), )), sectionName=sectName, thicknessAssignment=FROM_SECTION)

	#Assign beam orientation
	M.parts[partName].assignBeamSectionOrientation(method=
	    N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 0.0), ), )))




def createBeam(M, length, mat, partName):
	'''
	Creates a HEB 300 beam

	M:		 model
	length:  lenght of beam
	mat:	 material
	'''
	
	sectName = "HEB300"

	#Create Section and profile
	#HEB 550
	M.IProfile(b1=300.0, b2=300.0, h=300.0, l=150.0, name=
	    'Profile-2', t1=19.0, t2=19.0, t3=11.0)	#Now IPE profile, see ABAQUS for geometry definitions

	M.BeamSection(consistentMassMatrix=False, integration=
	    DURING_ANALYSIS, material=mat, name=sectName, poissonRatio=0.3, 
	    profile='Profile-2', temperatureVar=LINEAR)

	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize=10000.0)
	M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(length, 0.0))
	M.Part(dimensionality=THREE_D, name=partName, type=DEFORMABLE_BODY)
	M.parts[partName].BaseWire(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']

	#Assign section
	M.parts[partName].SectionAssignment(offset=0.0, 
	    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 
	    0.0), ), )), sectionName=sectName, thicknessAssignment=FROM_SECTION)

	#Assign beam orientation
	M.parts[partName].assignBeamSectionOrientation(method=
	    N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 0.0), ), )))




def createSlab(M, t, mat, dim, rebarMat, partName):
	'''
	Creates a square slab with thickness 200.0

	M:	      Model
	t:	  	  Thickness of slab
	mat:  	  Material of section
	dim:	  Dimention of square
	rebarMat: Material of rebars
	'''

	sectName = "Slab"

	rebarDim = 20.0			#mm^2 diameter
	rebarArea = 3.1415*(rebarDim/2.0)**2		#mm^2
	rebarSpacing = 120.0		#mm
	rebarPosition = -80.0		#mm distance from center of section

	#Create Section
	M.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
	    integrationRule=SIMPSON, material=mat, name=sectName, numIntPts=5, 
	    poissonDefinition=DEFAULT, preIntegrate=OFF,
	    temperature=GRADIENT, thickness=t, thicknessField='',
	    thicknessModulus=None, thicknessType=UNIFORM, useDensity=OFF)

	# Add rebars to section (both directions)
	M.sections[sectName].RebarLayers(layerTable=(
	    LayerProperties(barArea=rebarArea, orientationAngle=0.0,
	    barSpacing=rebarSpacing, layerPosition=rebarPosition,
	    layerName='Layer 1', material=rebarMat), 
	    LayerProperties(barArea=rebarArea, orientationAngle=90.0,
		barSpacing=rebarSpacing, layerPosition=rebarPosition,
		layerName='Layer 2', material=rebarMat)), 
	    rebarSpacing=CONSTANT)	
		
	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize= 10000.0)
	M.sketches['__profile__'].rectangle(point1=(0.0, 0.0),
		point2=(dim, dim))
	M.Part(dimensionality=THREE_D, name=partName, type=DEFORMABLE_BODY)
	M.parts[partName].BaseShell(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']

	#Assign section
	M.parts[partName].SectionAssignment(offset=0.0, 
	    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
	    faces=M.parts[partName].faces.findAt(((0.0, 
	    0.0, 0.0), ), )), sectionName='Slab', 
	    thicknessAssignment=FROM_SECTION)

	#Assign Rebar Orientation
	M.parts[partName].assignRebarOrientation(
	    additionalRotationType=ROTATION_NONE, axis=AXIS_1,
	    fieldName='', localCsys=None, orientationType=GLOBAL,
	    region=Region(faces=M.parts[partName].faces.findAt(
	    ((0.1, 0.1, 0.0), (0.0, 0.0, 1.0)), )))




def createSets(M, col_height):
	'''
	Create part sets. Will be available in assembly as well.
	Naming in assembly: partName_an-e.setName (an-e are coordinates)
	
	M:		Model
	'''

	# Column base/top
	M.parts['COLUMN'].Set(name='col-base', vertices=
	    M.parts['COLUMN'].vertices.findAt(((0.0, 0.0, 0.0),)))		
	M.parts['COLUMN'].Set(name='col-top', vertices=
	    M.parts['COLUMN'].vertices.findAt(((0.0, col_height, 0.0),)))

	#Column
	M.parts['COLUMN'].Set(edges=
	    M.parts['COLUMN'].edges.findAt(((0.0, 1.0, 0.0), )), 
	    name='set')

	#Beam
	M.parts['BEAM'].Set(edges=
	    M.parts['BEAM'].edges.findAt(((1.0, 0.0, 0.0), )), 
	    name='set')

	#Slab
	M.parts['SLAB'].Set(faces=
	    M.parts['SLAB'].faces.findAt(((1.0, 1.0, 0.0), )), 
	    name='set')



def createSurfs(M):
	'''
	Create part surfaces. Will be available in assembly as well.
	Naming in assembly: partName_an-e.surfName (an-e are coordinates)
	
	Parameters
	M:		Model
	'''

	#Slab top and bottom
	M.parts['SLAB'].Surface(name='botSurf', side1Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))
	M.parts['SLAB'].Surface(name='topSurf', side2Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))


	#Circumferential beam surfaces
	circumEdges = M.parts['BEAM'].edges.findAt(((2000.0, 0.0, 0.0), ))
	M.parts['BEAM'].Surface(circumEdges=circumEdges, name='surf')


	#Create circumferential column surfaces
	circumEdges = M.parts['COLUMN'].edges.findAt(((0.0, 10.0, 0.0), ))
	M.parts['COLUMN'].Surface(circumEdges=circumEdges, name='surf')

	


def createAssembly(M, x, z, y, x_d, z_d, y_d):
	'''
	Creates an assembly of columns, beams and slabs.

	Parameters:
	M:		Model
	x,z,y:	Nr of bays and floors
	x_d:	Size of bays in x direction
	z_d:	Size of bays in z direction
	y_d:	Floor height
	'''

	#Create coordinate list
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
				inst = 'COLUMN_' + a + n + "-" + e
				columnList.append(inst)
				#import and name instance
				M.rootAssembly.Instance(dependent=ON,
					name= inst,
					part=M.parts['COLUMN'])
				#Translate instance in x,y and z
				M.rootAssembly.translate(instanceList=(inst, ),	
					vector=(x_d*count , y_d*(int(e)-1),
					z_d*(int(n)-1)))

	#================ Beams ==================#
	#Beams in x (alpha) direction
	for a in range(len(alph)-1):
		for n in range(len(numb)-0):
			for e in range(len(etg)):
				inst = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]		
				beamList.append(inst)
				#import and name instance
				M.rootAssembly.Instance(dependent=ON,name=inst,
					part=M.parts['BEAM'])
				M.rootAssembly.translate(instanceList=(inst, ),
					vector=(x_d*a , y_d*(e+1), z_d*n))

	#Beams in z (numb) direction
	#a=0
	for a in [0,x-1]:
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'BEAM_'+ alph[a]+numb[n] + "-" + alph[a]+ \
					numb[n+1] + "-"+etg[e]
				beamList.append(inst)
				# import and name instance
				M.rootAssembly.Instance(dependent=ON,name=inst,
					part=M.parts['BEAM'])
				# Rotate instance
				M.rootAssembly.rotate(angle=-90.0, axisDirection=(
					0.0,1.0, 0.0), axisPoint=(0.0, 0.0, 0.0),
					instanceList=(inst, ))
				# Translate instance in x,y and z
				M.rootAssembly.translate(instanceList=(inst, ),
					vector=(x_d*a , y_d*(e+1), z_d*n))	


	#================ Slabs ==================#
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				slabList.append(inst)
				M.rootAssembly.Instance(dependent=ON,name=inst,
					part=M.parts['SLAB'])
				M.rootAssembly.rotate(angle=90.0,
					axisDirection=(1.0,0.0, 0.0),
					axisPoint=(0.0, 0.0, 0.0),
					instanceList=(inst, ))
				M.rootAssembly.translate(instanceList=(inst, ),
					vector=(x_d*a,y_d*(e+1),z_d*(n)))



def mesh(M, seed, slabSeedFactor):
	'''
	Meshes all parts with a global seed.
	Seed of slab may be different with a factor slabSeedFactor


	Parameters.
	M:		Model
	seed:	Global seed
	slabSeedFactor: Factor for having a different slab seed
	'''

	#Same seed for beam and column
	seed1 = seed2 = seed
	seed3 = seed*slabSeedFactor

	analysisType = STANDARD  #Could be STANDARD or EXPLICIT
		#This only controls what elements are available to choose from

	element1 = B31 #B31 or B32 for linear or quadratic
	element2 = element1
	element3 = S4R 	#S4R or S8R for linear or quadratic
					#(S8R is not available for Explicit)

	#================ Column ==================#
	#Seed
	M.parts['COLUMN'].seedPart(minSizeFactor=0.1, size=seed1)
	#Change element type
	M.parts['COLUMN'].setElementType(elemTypes=(ElemType(
		elemCode=element1, elemLibrary=analysisType), ), regions=(
		M.parts['COLUMN'].edges.findAt((0.0, 0.0, 0.0), ), ))
	#Mesh
	M.parts['COLUMN'].generateMesh()

	#================ Beam ==================#
	#Seed
	M.parts['BEAM'].seedPart(minSizeFactor=0.1, size=seed2)
	#Change element type
	M.parts['BEAM'].setElementType(elemTypes=(ElemType(
		elemCode=element2, elemLibrary=analysisType), ), regions=(
		M.parts['BEAM'].edges.findAt((0.0, 0.0, 0.0), ), ))
	#Mesh
	M.parts['BEAM'].generateMesh()

	#================ Slab ==================#
	#Seed
	M.parts['SLAB'].seedPart(minSizeFactor=0.1, size=seed3)
	#Change element type
	M.parts['SLAB'].setElementType(elemTypes=(ElemType(
		elemCode=S4R, elemLibrary=analysisType, secondOrderAccuracy=OFF, 
		hourglassControl=DEFAULT), ElemType(elemCode=S3R,
		elemLibrary=analysisType)), 
		regions=(M.parts['SLAB'].faces.findAt((0.0, 0.0, 0.0), ), ))
	#Mesh
	M.parts['SLAB'].generateMesh()





def elmCounter(M):
	'''
	Counts the total number of elements in model M.

	Returns:
	Number of elements
	'''
	nrElm = 0
	for inst in M.rootAssembly.instances.values():
		n = len(inst.elements)
		nrElm = nrElm + n
	return nrElm





def createJoints(M, x, z, y, x_d, z_d, y_d):
	'''
	Joins beams, columns and slabs with constraints.
	Beams are joined to columns with with MPC
	Columns are joined to columns with MPC
	Slabs are tied to beams with tie constrains.
	Slabs are only tied to beams in x direction to create one way slabs.

	Parameters:
	M:		Model
	x,z,y:	Nr of bays and floors
	x_d:	Size of bays in x direction
	z_d:	Size of bays in z direction
	y_d:	Floor height
	'''

	#MPC type for beam to column joints
	beamMPC = TIE_MPC	#May be TIE/BEAM/PIN (Tie will fix)
	colMPC = TIE_MPC



	#Set coordinates to Cartesian
	M.rootAssembly.DatumCsysByDefault(CARTESIAN)

	#Create coordinate list
	#Letters go left to right (positive x)
	#Number top to bottom (positive z)
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	etg = map(str,range(1,y+1))

	#Lists of all instances
	columnList = []
	beamList = []
	slabList = []



	#=========== Beams to columns  ============#
	

	#Column to beam in x(alpha) direction
	for a in range(len(alph)-1):
		for n in range(len(numb)):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),\
					csys=None, mpcType=beamMPC,
					name=constrName, surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)

	#Column to beam in negative x(alpha) direction
	for a in range(len(alph)-1, 0,-1):
		for n in range(len(numb)):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a-1]+numb[n] + "-" + \
					alph[a]+numb[n] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a-1]+numb[n] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					csys=None, mpcType=beamMPC, 
					name=constrName, surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )), userMode=DOF_MODE_MPC, userType=0)

	#Column to beam in z(num) direction
	for a in [0,x-1]:
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a]+numb[n+1] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a]+numb[n+1] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					csys=None, mpcType=beamMPC, name=constrName,
					surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)

	#Column to beam in negative z(num) direction
	for a in [0,x-1]:
		for n in range(len(numb)-1,0,-1):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a]+numb[n-1] + "-" +\
					alph[a]+numb[n] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a]+numb[n-1] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),\
					csys=None, mpcType=beamMPC, name=constrName,
					surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)




	#================ Column to column joints =============#

	for a in range(len(alph)):
		for n in range(len(numb)):
			for e in range(len(etg)-1):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				col2 = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e+1]
				constrName = 'Const_col_col_'+ alph[a]+numb[n] + "-"+ \
					etg[e] + "-"+etg[e+1]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					csys=None, mpcType=colMPC, name=constrName,
					surface=Region(
					vertices=M.rootAssembly.instances[col2].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)
		



	#================ Slabs to beams =============#
	#Uses tie and not MPC


	#Join beam surfaces that are to be constrained
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				beam1 = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]
				beam2 = 'BEAM_'+ alph[a]+numb[n+1] + "-" + \
					alph[a+1]+numb[n+1] + "-"+etg[e]
				M.rootAssembly.SurfaceByBoolean(name=inst+'_beamEdges', 
					surfaces=(
					M.rootAssembly.instances[beam1].surfaces['surf'],
					M.rootAssembly.instances[beam2].surfaces['surf']
					))

	#=========== Slab edge surfaces  ============#
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				M.rootAssembly.Surface(name=inst+'_edges', side1Edges=
					M.rootAssembly.instances[inst].edges.findAt(
					((x_d*a+1, y_d*(e+1), z_d*n), ),
					((x_d*a+1, y_d*(e+1), z_d*n+x_d), ),
					))

	#Tie slabs to beams (beams as master)
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				M.Tie(adjust=ON, master=
					M.rootAssembly.surfaces[inst+'_beamEdges'],
					name=inst, positionToleranceMethod=COMPUTED, slave=
					M.rootAssembly.surfaces[inst+'_edges']
					, thickness=OFF, tieRotations=OFF)



def mergeColBase(M,x,z):
	
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))

	lst=[]
	for a in alph:
		for n in numb:
			inst = 'COLUMN_' + a + n + "-1"
			lst.append(M.rootAssembly.allInstances[inst].sets['col-base'])

	tpl = tuple(lst)
	M.rootAssembly.SetByBoolean(name='col-bases', sets=tpl)









#=====================================================#
#=====================================================#
#                   Output                            #
#=====================================================#
#=====================================================#


def xyColBaseR2(modelName,x,z):
	odb = func.open_odb(modelName)
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





def xyForceDisp(modelName, x, z):
	odb=func.open_odb(modelName)

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




def xyUtopCol(modelName, column):
	'''
	Prints U1, U2 and U3 at top of column.

	modelName     = name of odb
	column      = name of column that is removed in APM
	printFormat = TIFF, PS, EPS, PNG, SVG
	stepName    = name of a step that exist in the model
	'''

	
	#Open ODB
	odb = func.open_odb(modelName)
	
	#Find correct node number and name of column
	nodeSet = odb.rootAssembly.instances[column].nodeSets['COL-TOP']
	nodeNr = nodeSet.nodes[0].label
	
	u1Name ='Spatial displacement: U1 PI: '+column+' Node '+str(nodeNr)+\
		' in NSET COL-TOP'
	u2Name ='Spatial displacement: U2 PI: '+column+' Node '+str(nodeNr)+\
		' in NSET COL-TOP'
	u3Name ='Spatial displacement: U3 PI: '+column+' Node '+str(nodeNr)+\
		' in NSET COL-TOP'

	#Create XY-Data
	xyU1colTop = xyPlot.XYDataFromHistory(odb=odb,
		outputVariableName=u1Name, suppressQuery=True, name='U1colTop')
	xyU2colTop = xyPlot.XYDataFromHistory(odb=odb,
		outputVariableName=u2Name, suppressQuery=True, name='U2colTop')
	xyU3colTop = xyPlot.XYDataFromHistory(odb=odb,
		outputVariableName=u3Name, suppressQuery=True, name='U3colTop')
	
	func.XYplot(modelName, plotName='U1colTop',
		xHead ='Time [s]',
		yHead = 'Displacement [mm]',
		xyDat= xyU1colTop)
	func.XYplot(modelName, plotName='U2colTop',
		xHead ='Time [s]',
		yHead = 'Displacement [mm]',
		xyDat= xyU2colTop)
	func.XYplot(modelName, plotName='U3colTop',
		xHead ='Time [s]',
		yHead = 'Displacement [mm]',
		xyDat= xyU3colTop)


def xyAPMcolPrint(modelName, column):
	'''
	Prints U2 at top of removed column in APM.

	modelName     = name of odb
	column      = name of column that is removed in APM
	printFormat = TIFF, PS, EPS, PNG, SVG
	stepName    = name of a step that exist in the model
	'''

	
	#Open ODB
	odb = func.open_odb(modelName)
	
	#Find correct node number and name of column
	nodeSet = odb.rootAssembly.instances[column].nodeSets['COL-TOP']
	nodeNr = nodeSet.nodes[0].label
	varName ='Spatial displacement: U2 PI: '+column+' Node '+str(nodeNr)+\
		' in NSET COL-TOP'

	#Create XY-curve
	xyU2colTop = xyPlot.XYDataFromHistory(odb=odb, outputVariableName=varName, 
		suppressQuery=True, name='U2colTop')
	
	func.XYplot(modelName, plotName='U2colTop',
		xHead ='Time [s]',
		yHead = 'Displacement [mm]',
		xyDat=xyU2colTop)
