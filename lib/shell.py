#Abaqus modules
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

import func




#==============================================================#
#==============================================================#
#                 CREATE SHELL GEOMETRY                        #
#==============================================================#
#==============================================================#


def createShellmod(modelName, x, z, y, steel, concrete, rebarSteel, seed):

	col_height = 7500.0
	beam_len = 3000.0

	M=mdb.models[modelName]




	#=========== Sections  ============#
	# HUP 300x300
	# HEB 300 beam

	M.HomogeneousShellSection(
		name='10mm',
		thickness=10.0,
		idealization=NO_IDEALIZATION, 
		integrationRule=SIMPSON, material=steel, numIntPts=5, 
		poissonDefinition=DEFAULT, preIntegrate=OFF,
		temperature=GRADIENT, thicknessField='',
		thicknessModulus=None, thicknessType=UNIFORM, useDensity=OFF)

	M.HomogeneousShellSection(
		name='11mm',
		thickness=11.0,

		idealization=NO_IDEALIZATION, 
	    integrationRule=SIMPSON, material=steel, numIntPts=5, 
	    poissonDefinition=DEFAULT, preIntegrate=OFF,
	    temperature=GRADIENT, thicknessField='',
	    thicknessModulus=None, thicknessType=UNIFORM, useDensity=OFF)

	M.HomogeneousShellSection(
		name='19mm',
		thickness=19.0,

		idealization=NO_IDEALIZATION, 
	    integrationRule=SIMPSON, material=steel, numIntPts=5, 
	    poissonDefinition=DEFAULT, preIntegrate=OFF,
	    temperature=GRADIENT, thicknessField='',
	    thicknessModulus=None, thicknessType=UNIFORM, useDensity=OFF)

	#Concrete section
	M.HomogeneousShellSection(
		name='SLAB', material=concrete, 
		idealization=NO_IDEALIZATION, 
	    integrationRule=SIMPSON, numIntPts=5, 
	    poissonDefinition=DEFAULT, preIntegrate=OFF,
	    temperature=GRADIENT, thickness=200.0, thicknessField='',
	    thicknessModulus=None, thicknessType=UNIFORM, useDensity=OFF)

	#Add rebars to section
	rebarDim = 20.0			#mm^2 diameter
	rebarArea = 3.1415*(rebarDim/2.0)**2		#mm^2
	rebarSpacing = 120.0		#mm
	rebarPosition = -80.0		#mm distance from center of section

	M.sections['SLAB'].RebarLayers(layerTable=(
	    LayerProperties(barArea=rebarArea, orientationAngle=0.0,
	    barSpacing=rebarSpacing, layerPosition=rebarPosition,
	    layerName='Layer 1', material=rebarSteel), ), 
	    rebarSpacing=CONSTANT)
	M.sections['SLAB'].RebarLayers(layerTable=(
	    LayerProperties(barArea=rebarArea, orientationAngle=90.0,
	    barSpacing=rebarSpacing, layerPosition=rebarPosition,
	    layerName='Layer 2', material=rebarSteel), ), 
	    rebarSpacing=CONSTANT)




	#=========== Column part  ============#
	dep=ON
	b=300.0
	s= M.ConstrainedSketch(name='__profile__', sheetSize=x*beam_len)
	point1=(0.5*b , 0.5*b)
	point2=(-0.5*b , -0.5*b)
	s.rectangle(point1=point1, point2=point2)


	M.Part(dimensionality=THREE_D, name='COLUMN', type=
	    DEFORMABLE_BODY)
	M.parts['COLUMN'].BaseShellExtrude(
		depth=col_height*y+0.5*b,
		sketch=s)
	del s

	#Assign section
	faces =M.parts['COLUMN'].faces.findAt(
		((-150.0, 0.0,  100.0), (0.0, -1.0, 0.0)),
		((150.0, 0.0, 100.0), (0.0, -1.0, 0.0)),
		((0.0, -150.0, 100.0), (0.0, -1.0, 0.0)),
		((0.0, 150.0, 100.0), (0.0, -1.0, 0.0)), )

	M.parts['COLUMN'].SectionAssignment(offset=0.0, offsetField='',
		offsetType=MIDDLE_SURFACE, region=Region(faces=faces), 
		sectionName='10mm', thicknessAssignment=FROM_SECTION)

	#Create bottom set
	M.parts['COLUMN'].Set(name='colBot',
		edges=M.parts['COLUMN'].edges.findAt(
		((   0.0,  150.0,  0.0),),
		(( 150.0,    0.0,  0.0),),
		((-150.0,    0.0,  0.0),),
		((   0.0, -150.0,  0.0),), ))

	#Create surface
	M.parts['COLUMN'].Surface(name='column', side12Faces=
	    M.parts['COLUMN'].faces.findAt(
		(( 150.0,   50.0, 100.0), ),
		((  50.0, -150.0, 100.0), ),
		((-150.0,  -50.0, 100.0), ),
		((-50.0,   150.0, 100.0), ), ))



	#=========== Beam part  ============#
	s = M.ConstrainedSketch(name='__profile__', sheetSize=
	200.0)
	s.Line(point1 = (0.0, -150.0), point2 = (0.0,150.0))
	s.Line(point1 = (-150.0, 150.0), point2 = (150.0, 150.0))
	s.Line(point1 = (-150.0, -150.0), point2 = (150.0, -150.0))
	M.Part(dimensionality=THREE_D, name='BEAM', type=
	DEFORMABLE_BODY)
	M.parts['BEAM'].BaseShellExtrude(depth=beam_len-b, sketch=s)
	del s

	#Assign section
	faces =M.parts['BEAM'].faces.findAt(
		((-50.0, 150.0,  100.0), (0.0, -1.0, 0.0)),
		((50.0, 150.0, 100.0), (0.0, -1.0, 0.0)),
		((-50.0, -150.0, 100.0), (0.0, -1.0, 0.0)),
		((50.0, -150.0, 100.0), (0.0, -1.0, 0.0)), )

	M.parts['BEAM'].SectionAssignment(offset=0.0, offsetField='',
		offsetType=MIDDLE_SURFACE, region=Region(faces=faces), 
		sectionName='19mm', thicknessAssignment=FROM_SECTION)

	faces =M.parts['BEAM'].faces.findAt(
		((0.0, 10.0,  100.0), (0.0, -1.0, 0.0)), )

	M.parts['BEAM'].SectionAssignment(offset=0.0, offsetField='',
		offsetType=MIDDLE_SURFACE, region=Region(faces=faces), 
		sectionName='11mm', thicknessAssignment=FROM_SECTION)

	#Surface
	M.parts['BEAM'].Surface(name='beam', side12Faces=
	    M.parts['BEAM'].faces.findAt(
		((  0.0,   50.0, 100.0), ),
		((-50.0,  150.0, 100.0), ),
		(( 50.0,  150.0, 100.0), ),
		((-50.0, -150.0, 100.0), ),
		(( 50.0, -150.0, 100.0), ), )
	    )




	#=========== Slab part  ============#		
	#Create part
	gap = seed
	s = M.ConstrainedSketch(name='__profile__', sheetSize= 10000.0)
	s.rectangle(point1=(0.0, 0.0), point2=(beam_len-b-2*gap, beam_len))

	M.Part(dimensionality=THREE_D, name='SLAB', type=DEFORMABLE_BODY)
	M.parts['SLAB'].BaseShell(sketch=s)
	del s

	#Assign section
	M.parts['SLAB'].SectionAssignment(offset=0.0, 
	    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
	    faces=M.parts['SLAB'].faces.findAt(((0.0, 
	    0.0, 0.0), ), )), sectionName='SLAB', 
	    thicknessAssignment=FROM_SECTION)

	#Assign Rebar Orientation
	M.parts['SLAB'].assignRebarOrientation(
	    additionalRotationType=ROTATION_NONE, axis=AXIS_1,
	    fieldName='', localCsys=None, orientationType=GLOBAL,
	    region=Region(faces=M.parts['SLAB'].faces.findAt(
	    ((0.1, 0.1, 0.0), (0.0, 0.0, 1.0)), )))

	#Slab surf top and bottom
	M.parts['SLAB'].Surface(name='topSurf', side2Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))
	M.parts['SLAB'].Surface(name='botSurf', side1Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))





	#=========== Assembly  ============#
	#Columns
	colNr=0
	for a in range(x):
		for n in range(z):
			colNr = colNr +1
			inst = 'COLUMN-'+str(colNr)
			M.rootAssembly.Instance(
				name = inst,
				dependent=dep,
				part=M.parts['COLUMN'])
			#Rotate
			M.rootAssembly.rotate(angle=-90.0,
				axisDirection=(1.0,0.0, 0.0),
				axisPoint=(0.0, 0.0, 0.0),
				instanceList=(inst, ))
			#Translate instance in x,y and z
			M.rootAssembly.translate(instanceList=(inst, ),	
				vector=(a*beam_len , 0, n*beam_len))
			

	#Beams in x- direction
	beamNr = 0
	for a in range(x-1):
		for n in range(z):
			for etg in range(y):
				beamNr = beamNr+1
				inst = 'BEAM-'+str(beamNr)
				M.rootAssembly.Instance(
					name = inst,
					dependent = dep,
					part=M.parts['BEAM'])
				#Rotate
				M.rootAssembly.rotate(angle=90.0,
					axisDirection=(0.0,1.0, 0.0),
					axisPoint=(0.0, 0.0, 0.0),
					instanceList=(inst, ))
				#Translate instance in x,y and z
				M.rootAssembly.translate(instanceList=(inst, ),	
					vector=(b*0.5+(beam_len)*a,(etg+1)*col_height,n*beam_len))
	
	#Beams in z-direction
	for a in range(x):
		for n in range(z-1):
			for etg in range(y):
				beamNr = beamNr+1
				inst = 'BEAM-'+str(beamNr)
				M.rootAssembly.Instance(
					name = inst,
					dependent = dep,
					part=M.parts['BEAM'])
				#Translate instance in x,y and z
				M.rootAssembly.translate(instanceList=(inst, ),	
					vector=(beam_len*a,(etg+1)*col_height,b*0.5+n*beam_len))

	#Slabs
	slabNr = 0
	for a in range(x-1):
		for n in range(z-1):
			for etg in range(y):
				slabNr = slabNr+1
				inst = 'SLAB-'+str(slabNr)
				M.rootAssembly.Instance(
					name = inst,
					dependent = dep,
					part = M.parts['SLAB'])
				#Rotate
				M.rootAssembly.rotate(angle =90,
					axisDirection=(1.0, 0.0, 0.0),
					axisPoint=(0.0,0.0,0.0),
					instanceList=(inst,))
				#Translate
				M.rootAssembly.translate(instanceList=(inst,),
					vector=
					(0.5*b+gap+a*beam_len, 0.5*b+(etg+1)*col_height, n*beam_len))



	#=========== Merge instances  ============#
	instLst = []
	for key in M.rootAssembly.instances.keys():
		instLst.append(M.rootAssembly.instances[key])
	instTup	= tuple(instLst)
	M.rootAssembly.InstanceFromBooleanMerge(domain=GEOMETRY
	    , instances=instTup, name='Part-1'
	    , originalInstances=DELETE,
	    keepIntersections=ON)



	#=========== Mesh  ============#
	seed = 150
	M.parts['Part-1'].seedPart(deviationFactor=0.1, 
	    minSizeFactor=0.1, size=seed)
	M.parts['Part-1'].generateMesh()

	#Write nr of elements to results file
	nrElm = len(M.parts['Part-1'].elements)
	with open('results.txt', 'a') as f:
		f.write("%s	Elements: %s \n" %(modelName, nrElm))


	#=========== BC  ============#
	#Fix column feet
	M.DisplacementBC(amplitude=UNSET, createStepName=
		'Initial', distributionType=UNIFORM, fieldName='',
		localCsys=None, name='BC-1', 
		region=M.rootAssembly.sets['Part-1-1.colBot'],
		u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET)

