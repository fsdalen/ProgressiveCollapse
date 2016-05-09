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









#====================================================#
#====================================================#
#                   Blast                            #
#====================================================#
#====================================================#

def conWep(modelName, TNT, blastType, coordinates,timeOfBlast, stepName):
	'''
	blastType = AIR_BLAST SURFACE_BLAST
	name of surf must be blastSurf

	time: Time of blast, NB: total time
OfBlast	'''
	M=mdb.models[modelName]

	#Create interaction property
	M.IncidentWaveProperty(definition= blastType,
	    massTNT=TNT,
	    massFactor=1.0e3,
	    lengthFactor=1.0e-3,
	    pressureFactor=1.0e6,
	    name='IntProp-1',)

	#Source Point
	feature = M.rootAssembly.ReferencePoint(point=coordinates)
	ID = feature.id
	sourceRP = M.rootAssembly.referencePoints[ID]
	M.rootAssembly.Set(name='Source', referencePoints=(sourceRP,))
	
	

	#Create ineraction
	M.IncidentWave(createStepName=stepName, definition=CONWEP, 
	    detonationTime=timeOfBlast, interactionProperty='IntProp-1',
	 	name='Int-1',
	    sourcePoint=M.rootAssembly.sets['Source'], 
	    surface=M.rootAssembly.surfaces['blastSurf'])

















#==============================================================#
#==============================================================#
#                   Create geometry                            #
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
























#===========================================================#
#===========================================================#
#                  SIMPLE MODEL                            #
#===========================================================#
#===========================================================#

def createSingleBeam(modelName, steel, seed):
	# HUP 300x300
	M=mdb.models[modelName]


	thickness=10.0 	#Thickness of section
	width=300.0-thickness
	hight= 3000.0


	#=========== Section  ============#
	sectName = 'HUP300x300'

	M.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
	    integrationRule=SIMPSON, material=steel, name=sectName, numIntPts=5, 
	    poissonDefinition=DEFAULT, preIntegrate=OFF,
	    temperature=GRADIENT, thickness=thickness, thicknessField='',
	    thicknessModulus=None, thicknessType=UNIFORM, useDensity=OFF)


	#=========== Extruded part  ============#	
	M.ConstrainedSketch(name='__profile__', sheetSize=width)
	M.sketches['__profile__'].rectangle(
		point1=(-0.5*width, -0.5*width), point2=(0.5*width, 0.5*width))
	M.Part(dimensionality=THREE_D, name='Part-1', type=
	    DEFORMABLE_BODY)
	M.parts['Part-1'].BaseShellExtrude(depth=hight, sketch=
	    M.sketches['__profile__'])
	del M.sketches['__profile__']

	#Assign section
	faces =M.parts['Part-1'].faces.findAt(((-145.0, 
		-48.333333, 0.0), (-1.0, 0.0, 0.0)), ((-48.333333, 145.0, 
		0.0), (0.0, 1.0, 0.0)), ((145.0, 48.333333, 0.0),
		(1.0, 0.0, 0.0)), ((48.333333, -145.0, 0.0),
		(0.0, -1.0, 0.0)), )

	M.parts['Part-1'].SectionAssignment(offset=0.0, offsetField=
		'', offsetType=MIDDLE_SURFACE, region=Region(faces=faces), 
		sectionName='HUP300x300', thicknessAssignment=FROM_SECTION)

	#Create sets
	M.parts['Part-1'].Set(edges=
	    M.parts['Part-1'].edges.findAt(
	    ((-145.0, -72.5, 0.0), ),
	    ((-72.5, 145.0, 0.0), ),
	    ((145.0, 72.5, 0.0), ),
	    ((72.5, -145.0, 0.0), ), ),
	    name='bot')

	M.parts['Part-1'].Set(edges=
	    M.parts['Part-1'].edges.findAt(
	    ((-145.0, -72.5, 3000.0), ),
	    ((-72.5, 145.0, 3000.0), ),
	    ((145.0, 72.5, 3000.0), ),
	    ((72.5, -145.0, 3000.0), ), ),
	    name='top')

	M.parts['Part-1'].DatumPlaneByPrincipalPlane(offset=
	    1500.0, principalPlane=XYPLANE)
	M.parts['Part-1'].PartitionFaceByDatumPlane(datumPlane=
	    M.parts['Part-1'].datums[5], faces=
	    M.parts['Part-1'].faces.findAt(((-48.333333, 145.0, 
	    2000.0), )))
	M.parts['Part-1'].PartitionEdgeByPoint(edge=
	    M.parts['Part-1'].edges.findAt((72.5, 145.0, 
	    1500.0), ), point=
	    M.parts['Part-1'].InterestingPoint(
	    M.parts['Part-1'].edges.findAt((72.5, 145.0, 
	    1500.0), ), MIDDLE))
	M.parts['Part-1'].Set(name='mid', vertices=
	    M.parts['Part-1'].vertices.findAt(((0.0, 145.0, 
	    1500.0), )))


	# #=========== Small plate just for pressure output  ============#
	# #Part
	# s = M.ConstrainedSketch(name='__profile__', sheetSize=
	#     200.0)
	# s.rectangle(
	# 	point1=(-75.0, 75.0),
	# 	point2=(75.0, -75.0))
	# M.Part(dimensionality=THREE_D, name='Part-2', 
	#     type=DEFORMABLE_BODY)
	# M.parts['Part-2'].BaseShell(sketch=s)
	# del s

	# #Set
	# face =M.parts['Part-2'].faces.findAt(((25.0,25.0,0.0),))
	# M.parts['Part-2'].Set(faces=face, name='face')

	# #Section
	# M.parts['Part-2'].SectionAssignment(offset=0.0, offsetField=
	# 	'', offsetType=MIDDLE_SURFACE, region=Region(faces=face), 
	# 	sectionName='HUP300x300', thicknessAssignment=FROM_SECTION)

	# #Mesh
	# seed = 150.0
	# M.parts['Part-2'].seedPart(deviationFactor=0.1, 
 #    minSizeFactor=0.1, size=seed)
	# M.parts['Part-2'].generateMesh()

	#=========== Assembly  ============#
	dep = ON
	M.rootAssembly.Instance(dependent=dep, name='Part-1-1',
		part=M.parts['Part-1'])
	M.rootAssembly.rotate(angle=-90.0,
		axisDirection=(1.0, 0.0, 0.0), axisPoint=(0.0, 0.0, 0.0),
		instanceList=('Part-1-1', ))


	# #Small plate
	# M.rootAssembly.Instance(dependent=ON, name='Part-2-1',
	# 	part=M.parts['Part-2'])
	# M.rootAssembly.rotate(
	# 	angle=90.0,	axisDirection=(0.0, 1.0, 0.0), axisPoint=(0.0, 0.0, 0.0),
	# 	instanceList=('Part-2-1', ))
	# M.rootAssembly.translate(
	# 	instanceList=('Part-2-1', ), vector=(-1000.0, 0.0, 0.0))

	#Create blast surface
	M.rootAssembly.Surface(name='blastSurf', side1Faces=
	    M.rootAssembly.instances['Part-1-1'].faces.findAt(((
	    -145.0, 0.0, 48.333333), ),
	    ((-48.333333, 0.0, -145.0), ), 
	    ((145.0, 0.0, -48.333333), ),
	    ((48.333333, 0.0, 145.0), ),))  # +\
		# M.rootAssembly.instances['Part-2-1'].faces.findAt(
		# ((-1000.0, 25.0, -25.0), )))	#Small plate

	#=========== Mesh  ============#
	M.parts['Part-1'].seedPart(deviationFactor=0.1, 
    minSizeFactor=0.1, size=seed)
	M.parts['Part-1'].generateMesh()
	
	#Create set for mid nodes
	nodes = M.parts['Part-1'].nodes[101:102]+\
		M.parts['Part-1'].nodes[120:121]+\
		M.parts['Part-1'].nodes[139:140]+\
		M.parts['Part-1'].nodes[158:159]
	M.parts['Part-1'].Set(nodes = nodes, name = 'midNodes')

	#=========== BC  ============#
	#Fix ends
	M.DisplacementBC(amplitude=UNSET, createStepName='Initial', 
	    distributionType=UNIFORM, fieldName='', localCsys=None, name='fix_top', 
	    region=M.rootAssembly.instances['Part-1-1'].sets['top'], 
	    u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET)
	
	M.DisplacementBC(amplitude=UNSET, createStepName='Initial', 
	    distributionType=UNIFORM, fieldName='', localCsys=None, name='fix_bot', 
	    region=M.rootAssembly.instances['Part-1-1'].sets['bot'], 
	    u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET)

	# #Fix small plate
	# M.DisplacementBC(amplitude=UNSET, createStepName=
	# 	'Initial', distributionType=UNIFORM, fieldName='',
	# 	localCsys=None, name='fix_Plate', region=
	# 	M.rootAssembly.instances['Part-2-1'].sets['face']
	# 	, u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET)






def xySimpleDef(modelName, printFormat):

	plotName = 'midU1'


	#Open ODB
	odb = func.open_odb(modelName)


	xy1 = xyPlot.XYDataFromHistory(odb=odb, 
	    outputVariableName='Spatial displacement: U1 PI: PART-1-1 Node 102 in NSET MIDNODES', 
	    suppressQuery=True)
	c1 = session.Curve(xyData=xy1)
	xy2 = xyPlot.XYDataFromHistory(odb=odb, 
	    outputVariableName='Spatial displacement: U1 PI: PART-1-1 Node 121 in NSET MIDNODES', 
	    suppressQuery=True)
	c2 = session.Curve(xyData=xy2)
	xy3 = xyPlot.XYDataFromHistory(odb=odb, 
	    outputVariableName='Spatial displacement: U1 PI: PART-1-1 Node 140 in NSET MIDNODES', 
	    suppressQuery=True)
	c3 = session.Curve(xyData=xy3)
	xy4 = xyPlot.XYDataFromHistory(odb=odb, 
	    outputVariableName='Spatial displacement: U1 PI: PART-1-1 Node 159 in NSET MIDNODES', 
	    suppressQuery=False)
	c4 = session.Curve(xyData=xy4)

	#Plot and Print
	func.XYprint(modelName, plotName, printFormat, c4)

	#Report data
	# tempFile = 'temp.txt'
	# session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy1, ))
	# func.fixReportFile(tempFile, 'frontU1', modelName)

	# tempFile = 'temp.txt'
	# session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy2, ))
	# func.fixReportFile(tempFile, 'middleU1', modelName)

	# tempFile = 'temp.txt'
	# session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy3, ))
	# func.fixReportFile(tempFile, 'backU1', modelName)

	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy4, ))
	func.fixReportFile(tempFile, 'otherMiddleU1', modelName)

def xySimpleIWCONWEP(modelName, printFormat):

	plotName = 'IWCONWEP'


	#Open ODB
	odb = func.open_odb(modelName)

	xyList = xyPlot.xyDataListFromField(odb=odb, outputPosition=ELEMENT_FACE, 
	    variable=(('IWCONWEP', ELEMENT_FACE), ),
	    elementSets=('PART-2-1.FACE', ))
	xy1 = xyList[0]
	# xyp = session.xyPlots['XYPlot-1']
	# chartName = xyp.charts.keys()[0]
	# chart = xyp.charts[chartName]
	# curveList = session.curveSet(xyData=xyList)
	# chart.setValues(curvesToPlot=curveList)
	# session.viewports['Viewport: 1'].setValues(displayedObject=xyp)
	c1 = session.Curve(xyData=xy1)
	#Plot and Print
	func.XYprint(modelName, plotName, printFormat, c1)

	#Report data
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF,
		xyData=(xy1, ))
	func.fixReportFile(tempFile, plotName, modelName)