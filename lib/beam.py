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

#Python modules
from datetime import datetime
import csv


import func




#============================================================#
#============================================================#
#               	Simple beam models                       #
#============================================================#
#============================================================#

def createSingleBeam(modelName, steel):

	M = mdb.models[modelName]
	#================ Part ==================#

	part1 = "COLUMN"
	sect1 = "HUP"
	col1_height = 4200.0

	#Create Section and profile
	M.BoxProfile(a=300.0, b=300.0, name='Profile-1', t1=10.0,
		uniformThickness=ON)
	M.BeamSection(consistentMassMatrix=False, integration=
	    DURING_ANALYSIS, material=steel, name=sect1, poissonRatio=0.3, 
	    profile='Profile-1', temperatureVar=LINEAR)
	#Fluid inertia of section
	airDensity = 1.225e-12    #1.225 kg/m^3
	M.sections[sect1].setValues(useFluidInertia=ON,
		fluidMassDensity=airDensity, crossSectionRadius=300.0, 
	    lateralMassCoef=1.15)#latteralMassCoef is for rectangle from wikipedia


	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize=20.0)
	M.sketches['__profile__'].Line(point1=(0.0, 0.0),
		point2=(0.0, col1_height))
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
	M.parts[part1].Set(name='col-base', vertices=
	    M.parts[part1].vertices.findAt(((0.0, 0.0, 0.0),)))     
	M.parts[part1].Set(name='col-top', vertices=
	    M.parts[part1].vertices.findAt(((0.0, col1_height, 0.0),)))

	#Partition
	p = M.parts['COLUMN']
	e = p.edges
	pickedRegions = e.findAt(((0.0, 1000.0, 0.0), ))
	p.deleteMesh(regions=pickedRegions)
	p = M.parts['COLUMN']
	e, v, d = p.edges, p.vertices, p.datums
	p.PartitionEdgeByPoint(edge=e.findAt(coordinates=(0.0, 1000.0, 0.0)), 
	    point=p.InterestingPoint(edge=e.findAt(
	    coordinates=(0.0, 1000.0, 0.0)), rule=MIDDLE))

	#Create set at middle
	p = M.parts['COLUMN']
	v = p.vertices
	verts = v.findAt(((0.0, 2100.0, 0.0), ))
	p.Set(vertices=verts, name='col-mid')

	#================ Mesh ==================#
	analysisType = STANDARD  #Could be STANDARD or EXPLICIT
	element1 = B31 #B31 or B32 for linear or quadratic

	#Seed
	seed=300.0
	M.parts[part1].seedPart(minSizeFactor=0.1, size=seed)

	#Change element type
	M.parts[part1].setElementType(elemTypes=(ElemType(
	    elemCode=element1, elemLibrary=analysisType), ), regions=(
	    M.parts[part1].edges.findAt((0.0, 0.0, 0.0), ), ))

	#Mesh
	M.parts[part1].generateMesh()


	#================ Instance ==================#
	M.rootAssembly.Instance(name='COLUMN-1', part=M.parts['COLUMN'],
		dependent=ON)


	#=========== Blast surface  ============#
	M.rootAssembly
	c1 = M.rootAssembly.instances['COLUMN-1'].edges
	circumEdges1 = c1.findAt(((0.0, 525.0, 0.0), ), ((0.0, 2625.0, 0.0), ))
	M.rootAssembly.Surface(circumEdges=circumEdges1, name='blastSurf')
	

	#================ BC ==================#
	region = M.rootAssembly.instances['COLUMN-1'].sets['col-base']
	M.DisplacementBC(name='BC-1', createStepName='Initial', 
	    region=region, u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET, 
	    amplitude=UNSET, distributionType=UNIFORM, fieldName='',
	    localCsys=None)

	region = M.rootAssembly.instances['COLUMN-1'].sets['col-top']
	M.DisplacementBC(name='BC-2', createStepName='Initial', 
	    region=region, u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET, 
	    amplitude=UNSET, distributionType=UNIFORM, fieldName='',
	    localCsys=None)



def xySimple(modelName, printFormat):

	#Open ODB
	odb = func.open_odb(modelName)


	#=========== Force-displacement  ============#
	plotName='force-Disp'
	rf1 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='Reaction force: RF1 PI: COLUMN-1 Node 1 in NSET COL-BASE')
	rf2 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='Reaction force: RF1 PI: COLUMN-1 Node 3 in NSET COL-TOP')
	u = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='Spatial displacement: U1 PI: COLUMN-1 Node 2 in NSET COL-MID')

	# rf1 = session.XYDataFromHistory(name='XYData-1', odb=odb,
	# 	outputVariableName='Reaction force: RF1 at Node 1 in NSET COL-BASE')
	# rf2 = session.XYDataFromHistory(name='XYData-2', odb=odb, 
	# 	outputVariableName='Reaction force: RF1 at Node 3 in NSET COL-TOP')
	# u = session.XYDataFromHistory(name='XYData-3', odb=odb, 
	# 	outputVariableName='Spatial displacement: U1 at Node 2 in NSET COL-MID')
	xy = combine(u, -(rf1+rf2))
	c1 = session.Curve(xyData=xy)
	func.XYprint(modelName, plotName, printFormat, c1)


	#=========== Displacement  ============#
	plotName = 'midU1'

	c1 = session.Curve(xyData=u)

	#Plot and Print
	func.XYprint(modelName, plotName, printFormat, c1)

	#Report data
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(u, ))
	func.fixReportFile(tempFile, plotName, modelName)






































#====================================================#
#====================================================#
#                   Blast                            #
#====================================================#
#====================================================#


def blast(modelName, stepName, sourceCo, refCo):
	airDensity = 1.225e-12    #1.225 kg/m^3
	soundSpeed =340.29e3    # 340.29 m/s

	M=mdb.models[modelName]

	#Pressure amplitude from file blastAmp.csv
	table=[]
	with open('blastAmp.csv', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		for row in reader:
			table.append((float(row[0]), float(row[1])))
			blastTime = float(row[0])

	tpl = tuple(table)
	M.TabularAmplitude(name='Blast', timeSpan=STEP, 
	   	smooth=SOLVER_DEFAULT, data=(tpl))


	#Source Point
	feature = M.rootAssembly.ReferencePoint(point=sourceCo)
	ID = feature.id
	sourceRP = M.rootAssembly.referencePoints[ID]
	M.rootAssembly.Set(name='Source', referencePoints=(sourceRP,))

	#Standoff Point
	feature = M.rootAssembly.ReferencePoint(point=refCo)
	ID = feature.id
	standoffRP = M.rootAssembly.referencePoints[ID]
	M.rootAssembly.Set(name='Standoff', referencePoints=(standoffRP,))


	#Create interaction property
	M.IncidentWaveProperty(name='Blast', 
	    definition=SPHERICAL, fluidDensity=airDensity, soundSpeed=soundSpeed)


	#Create incident Wave Interaction
	M.IncidentWave(name='Blast', createStepName=stepName, 
	    sourcePoint=M.rootAssembly.sets['Source'],
	    standoffPoint=M.rootAssembly.sets['Standoff'],
	    surface=M.rootAssembly.surfaces['blastSurf'],
	    definition=PRESSURE, interactionProperty='Blast', 
	    referenceMagnitude=1.0, amplitude='Blast')


	#Set model wave formulation (does not matter when fluid is not modeled)
	M.setValues(waveFormulation=TOTAL)






















































#===============================================================#
#===============================================================#
#                   Build beam model                            #
#===============================================================#
#===============================================================#


def buildBeamMod(modelName, x, z, y, steel, concrete, rebarSteel):
	M=mdb.models[modelName]


	#=========== Parts  ============#
	#Create Column
	col_height = 4000.0
	createColumn(M, height=col_height, mat=steel, partName='COLUMN')

	#Create Beam
	beam_len = 8000.0
	createBeam(M, length=beam_len, mat=steel, partName='BEAM')

	#Create slab
	createSlab(M, t=200.0, mat=concrete, dim=beam_len,
		rebarMat=rebarSteel, partName='SLAB')


	#=========== Sets and surfaces  ============#
	#A lot of surfaces are created with the joints
	createSets(M, col_height)
	createSurfs(M)


	#=========== Assembly  ============#
	createAssembly(M, x, z, y,
		x_d = beam_len, z_d = beam_len, y_d = col_height)


	#=========== Mesh  ============#
	seed = 800.0
	mesh(M, seed)

	#Write nr of elements to results file
	M.rootAssembly.regenerate()
	nrElm = elmCounter(M)
	with open('results.txt','a') as f:
		f.write("%s	Elements: %s \n" %(modelName, nrElm))


	#=========== Joints  ============#
	createJoints(M, x, z, y,
		x_d = beam_len, z_d = beam_len, y_d = col_height)


	#=========== Fix column base  ============#
	fixColBase(M, x, z)






#========================================================#
#========================================================#
#                   Functions                            #
#========================================================#
#========================================================#


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
	Creates a HEB 550 beam

	M:		 model
	length:  lenght of beam
	mat:	 material
	'''
	
	sectName = "HEB550"

	#Create Section and profile
	#HEB 550
	M.IProfile(b1=300.0, b2=300.0, h=550.0, l=275.0, name=
	    'Profile-2', t1=29.0, t2=29.0, t3=15.0)	#Now IPE profile, see ABAQUS for geometry definitions

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

	#Add rebars to section
	M.sections[sectName].RebarLayers(layerTable=(
	    LayerProperties(barArea=rebarArea, orientationAngle=0.0,
	    barSpacing=rebarSpacing, layerPosition=rebarPosition,
	    layerName='Layer 1', material=rebarMat), ), 
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
	M.parts['SLAB'].Surface(name='topSurf', side1Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))
	M.parts['SLAB'].Surface(name='botSurf', side2Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))


	#Circumferential beam surfaces
	circumEdges = M.parts['BEAM'].edges.findAt(((2000.0, 0.0, 0.0), ))
	M.parts['BEAM'].Surface(circumEdges=circumEdges, name='surf')



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
				M.rootAssembly.rotate(angle=-90.0, axisDirection=(
					1.0,0.0, 0.0), axisPoint=(0.0, 0.0, 0.0),
					instanceList=(inst, ))
				M.rootAssembly.translate(instanceList=(inst, ),
					vector=(x_d*a,y_d*(e+1),z_d*(n+1)))



def mesh(M, seed):
	'''
	Meshes all parts with a global seed

	Parameters.
	M:		Model
	seed:	Global seed
	'''

	#Same seed for all parts
	seed1 = seed2 = seed3 = seed

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


def fixColBase(M, x, z):
	'''
	Fixes all column bases

	Parameters:
	M: 		Model
	x, z 	Nr of bays
	'''

	#Create coordinate list
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))

	for a in alph:
		for n in numb:
			colSet = 'COLUMN_' + a + n + "-" + "1.col-base"
			M.DisplacementBC(amplitude=UNSET, createStepName=
				'Initial', distributionType=UNIFORM, fieldName='', fixed=OFF,
				localCsys=None, name=colSet, region=
				M.rootAssembly.sets[colSet], u1=0.0, u2=0.0, u3=0.0
				, ur1=0.0, ur2=0.0, ur3=0.0)



#===================================================#
#===================================================#
#               STEP DEPENDENT FUNCTIONS           	#
#===================================================#
#===================================================#

def addSlabLoad(M, x, z, y, step, load):
	'''
	Adds a surface traction to all slabs

	Parameters:
	M: 		 Model
	load: 	 Magnitude of load (positive y)
	x, z, y: Nr of bays
	Step:	 Which step to add the load
	'''

	#Create coordinate list
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	etg = map(str,range(1,y+1))

	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n]+"-"+etg[e]
				M.SurfaceTraction(createStepName=step, 
					directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
					distributionType=UNIFORM, field='', follower=OFF,
					localCsys=None, magnitude= load,
					name="Slab_" + alph[a]+numb[n]+"-"+etg[e],
					region=M.rootAssembly.instances[inst].surfaces['topSurf'],
					traction=GENERAL)
