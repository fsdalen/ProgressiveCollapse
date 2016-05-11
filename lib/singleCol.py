#Abaqus modules
from abaqus import *
from abaqusConstants import *
import xyPlot
from regionToolset import *

#Python modules
import csv

#Own modules
from lib import func as func


#=========================================================#
#=========================================================#
#                   BEAM MODEL                            #
#=========================================================#
#=========================================================#

def createSimpleBeamGeom(modelName, steel):

	M = mdb.models[modelName]
	#================ Part ==================#

	part1 = "COLUMN"
	sect1 = "HUP"
	col1_height = 3000.0

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
	verts = v.findAt(((0.0, 1500.0, 0.0), ))
	p.Set(vertices=verts, name='col-mid')

	#================ Mesh ==================#
	analysisType = EXPLICIT  #Could be STANDARD or EXPLICIT
	element1 = B31 #B31 or B32 for linear or quadratic

	#Seed
	seed=150.0
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


#=========== Post  ============#

def xySimpleBeam(modelName, printFormat):

	#Open ODB
	odb = func.open_odb(modelName)


	#=========== Force-displacement  ============#
	plotName='force-Disp'
	
	# rf1 = xyPlot.XYDataFromHistory(odb=odb, 
	# 	outputVariableName='Reaction force: RF1 PI: COLUMN-1 Node 1 in NSET COL-BASE')
	# rf2 = xyPlot.XYDataFromHistory(odb=odb, 
	# 	outputVariableName='Reaction force: RF1 PI: COLUMN-1 Node 3 in NSET COL-TOP')
	# u = xyPlot.XYDataFromHistory(odb=odb, 
	# 	outputVariableName='Spatial displacement: U1 PI: COLUMN-1 Node 2 in NSET COL-MID')

	rf1 = session.XYDataFromHistory(name='XYData-1', odb=odb,
		outputVariableName='Reaction force: RF1 at Node 1 in NSET COL-BASE')
	rf2 = session.XYDataFromHistory(name='XYData-2', odb=odb, 
		outputVariableName='Reaction force: RF1 at Node 3 in NSET COL-TOP')
	u = session.XYDataFromHistory(name='XYData-3', odb=odb, 
		outputVariableName='Spatial displacement: U1 at Node 2 in NSET COL-MID')
	fdData = combine(u, -(rf1+rf2))
	fdCurve = session.Curve(xyData=fdData)
	func.XYprint(modelName, plotName, printFormat, fdCurve)

	#Report data
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(fdData, ))
	func.fixReportFile(tempFile, plotName, modelName)


	#=========== Displacement  ============#
	plotName = 'midU1'

	dCurve = session.Curve(xyData=u)

	#Plot and Print
	func.XYprint(modelName, plotName, printFormat, dCurve)

	#Report data
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(u, ))
	func.fixReportFile(tempFile, plotName, modelName)






















#==========================================================#
#==========================================================#
#                   SHELL MODEL                            #
#==========================================================#
#==========================================================#




def createSimpleShellGeom(modelName, steel, seed):
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

	#Create surfaces
	M.rootAssembly.Surface(name='front', side1Faces=
	    M.rootAssembly.instances['Part-1-1'].faces.findAt(
	    ((-145.0, 0.0, 48.333333), ),))
	M.rootAssembly.Surface(name='back', side1Faces=
	    M.rootAssembly.instances['Part-1-1'].faces.findAt(
	    ((145.0, 0.0, -48.333333), ),))
	M.rootAssembly.Surface(name='sides', side1Faces=
	    M.rootAssembly.instances['Part-1-1'].faces.findAt(
	    ((-48.333333, 0.0, -145.0), ), 
	    ((48.333333, 0.0, 145.0), ),
	    ((-48.333333, 2000.0, -145.0), ),))
	# M.rootAssembly.Surface(name='smallPlate', side1Faces=
	# 	M.rootAssembly.instances['Part-2-1'].faces.findAt(
	# 	((-1000.0, 25.0, -25.0), )))
	

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











#=========== Loading  ============#



def pressureLoad(modelName, stepName, surf):
	M=mdb.models[modelName]

	#Pressure amplitude from file blastAmp.csv
	table=[]
	with open('inputData/blastAmp.csv', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		for row in reader:
			table.append((float(row[0]), float(row[1])))
			blastTime = float(row[0])

	tpl = tuple(table)
	M.TabularAmplitude(name='Blast', timeSpan=STEP, 
	   	smooth=SOLVER_DEFAULT, data=(tpl))

	#Pressure load
	M.Pressure(name='Load-1', createStepName=stepName, 
	    region=M.rootAssembly.surfaces[surf], distributionType=UNIFORM,
	    field='', magnitude=1.0, amplitude='blast')









#=========== Post  ============#


def xySimpleShell(modelName, printFormat):

	plotName = 'midU1'


	#Open ODB
	odb = func.open_odb(modelName)


	xy1 = xyPlot.XYDataFromHistory(odb=odb, 
	    outputVariableName='Spatial displacement: U1 at Node 4 in NSET MID', 
	    suppressQuery=True)
	c1 = session.Curve(xyData=xy1)
	# xy2 = xyPlot.XYDataFromHistory(odb=odb, 
	#     outputVariableName='Spatial displacement: U1 PI: PART-1-1 Node 121 in NSET MIDNODES', 
	#     suppressQuery=True)
	# c2 = session.Curve(xyData=xy2)
	# xy3 = xyPlot.XYDataFromHistory(odb=odb, 
	#     outputVariableName='Spatial displacement: U1 PI: PART-1-1 Node 140 in NSET MIDNODES', 
	#     suppressQuery=True)
	# c3 = session.Curve(xyData=xy3)
	# xy4 = xyPlot.XYDataFromHistory(odb=odb, 
	#     outputVariableName='Spatial displacement: U1 PI: PART-1-1 Node 159 in NSET MIDNODES', 
	#     suppressQuery=False)
	# c4 = session.Curve(xyData=xy4)

	#Plot and Print
	func.XYprint(modelName, plotName, printFormat, c1)

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
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy1, ))
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