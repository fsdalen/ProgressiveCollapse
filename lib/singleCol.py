#Abaqus modules
from abaqus import *
from mesh import *
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

def createSimpleBeamGeom(modelName, steel, seed):

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
	    lateralMassCoef=1.0) #1.0


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
	M.parts[part1].seedPart(minSizeFactor=0.1, size=seed)

	#Change element type
	M.parts[part1].setElementType(
		elemTypes=(ElemType(elemCode=element1, elemLibrary=analysisType,),),
		regions=(M.parts[part1].edges.findAt((0.0, 0.0, 0.0), ), ))


	#Mesh
	M.parts[part1].generateMesh()


	#================ Instance ==================#
	M.rootAssembly.Instance(name='COLUMN-1', part=M.parts['COLUMN'],
		dependent=ON)


	#=========== Blast surface  ============#
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

def xyBeam(modelName):

	#Open ODB
	odb = func.open_odb(modelName)


	#=========== Displacemnet  ============#
	#Get node numbers
	nodeNr = odb.rootAssembly.instances['COLUMN-1'].\
		nodeSets['COL-MID'].nodes[0].label

	#Create names
	name = 'Spatial displacement: U1 PI: COLUMN-1 Node '+\
		str(nodeNr)+' in NSET COL-MID'
	
	#Get xy data
	xyU1mid = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName=name)
	
	func.XYplot(modelName,
		plotName = 'U1mid',
		xHead='Time [s]',
		yHead='Displacement [mm]',
		xyDat=xyU1mid)
	

	#=========== Reaction Force  ============#
	#Get node numbers
	topNodeNr = odb.rootAssembly.instances['COLUMN-1'].\
		nodeSets['COL-TOP'].nodes[0].label
	baseNodeNr = odb.rootAssembly.instances['COLUMN-1'].\
		nodeSets['COL-BASE'].nodes[0].label

	#Create names
	topName = 'Reaction force: RF1 PI: COLUMN-1 Node '+\
		str(topNodeNr)+' in NSET COL-TOP'
	baseName = 'Reaction force: RF1 PI: COLUMN-1 Node '+\
		str(baseNodeNr)+' in NSET COL-BASE'

	#Get xy data
	xyR1top = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName=topName)
	xyR1base = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName=baseName)

	xyR1tot = sum(xyR1top,xyR1base)

	func.XYplot(modelName,
		plotName = 'R1',
		xHead='Time [s]',
		yHead='Force [N]',
		xyDat=xyR1tot)

	# #=========== Force-displacement  ============#
	# plotName='force-Disp'
	
	# rf1 = xyPlot.XYDataFromHistory(odb=odb, 
	# 	outputVariableName='Reaction force: RF1 PI: COLUMN-1 Node 1 in NSET COL-BASE')
	# rf2 = xyPlot.XYDataFromHistory(odb=odb, 
	# 	outputVariableName='Reaction force: RF1 PI: COLUMN-1 Node 3 in NSET COL-TOP')
	# u = xyPlot.XYDataFromHistory(odb=odb, 
	# 	outputVariableName='Spatial displacement: U1 PI: COLUMN-1 Node 2 in NSET COL-MID')

	xyUR = combine(xyU1mid, -xyR1tot)

	func.XYplot(modelName,
		plotName = 'ForceDisp',
		xHead='Displacement [mm]',
		yHead='Force [N]',
		xyDat=xyUR)














#==========================================================#
#==========================================================#
#                   SHELL MODEL                            #
#==========================================================#
#==========================================================#




def createSimpleShellGeom(modelName, steel, seed):
	# HUP 300x300
	M=mdb.models[modelName]


	thickness=10.0 	#Thickness of section
	width=300.0
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
	faces =M.parts['Part-1'].faces.findAt(((-150.0, 
		-48.333333, 0.0), (-1.0, 0.0, 0.0)), ((-48.333333, 150.0, 
		0.0), (0.0, 1.0, 0.0)), ((150.0, 48.333333, 0.0),
		(1.0, 0.0, 0.0)), ((48.333333, -150.0, 0.0),
		(0.0, -1.0, 0.0)), )

	M.parts['Part-1'].SectionAssignment(offset=0.0, offsetField=
		'', offsetType=MIDDLE_SURFACE, region=Region(faces=faces), 
		sectionName='HUP300x300', thicknessAssignment=FROM_SECTION)

	#Create sets
	M.parts['Part-1'].Set(edges=
	    M.parts['Part-1'].edges.findAt(
	    ((-150.0, -72.5, 0.0), ),
	    ((-72.5, 150.0, 0.0), ),
	    ((150.0, 72.5, 0.0), ),
	    ((72.5, -150.0, 0.0), ), ),
	    name='bot')

	M.parts['Part-1'].Set(edges=
	    M.parts['Part-1'].edges.findAt(
	    ((-150.0, -72.5, 3000.0), ),
	    ((-72.5, 150.0, 3000.0), ),
	    ((150.0, 72.5, 3000.0), ),
	    ((72.5, -150.0, 3000.0), ), ),
	    name='top')

	#Partition to obtain geometric points
	M.parts['Part-1'].DatumPlaneByPrincipalPlane(offset=
	    1500.0, principalPlane=XYPLANE)
	M.parts['Part-1'].PartitionFaceByDatumPlane(datumPlane=
	    M.parts['Part-1'].datums[5], faces=
	    M.parts['Part-1'].faces.findAt(
	    (( -50.0, 150.0, 2000.0),),
	    ((-150.0, -50.0, 2000.0),),
	    (( 150.0,  50.0, 2000.0),), ))
	M.parts['Part-1'].PartitionEdgeByPoint(edge=
	    M.parts['Part-1'].edges.findAt(
	    (72.5, 150.0, 1500.0), ),
	    point=M.parts['Part-1'].InterestingPoint(
	    M.parts['Part-1'].edges.findAt(
	    (72.5, 150.0, 1500.0), ), MIDDLE))
	M.parts['Part-1'].PartitionEdgeByPoint(edge=
	    M.parts['Part-1'].edges.findAt(
	    (-150.0, 75.0, 1500.0), ),
	    point=M.parts['Part-1'].InterestingPoint(
	    M.parts['Part-1'].edges.findAt(
	    (-150.0, 75.0, 1500.0), ), MIDDLE))
	M.parts['Part-1'].PartitionEdgeByPoint(edge=
	    M.parts['Part-1'].edges.findAt(
	    (150.0, -75.0, 1500.0), ),
	    point=M.parts['Part-1'].InterestingPoint(
	    M.parts['Part-1'].edges.findAt(
	    (150.0, -75.0, 1500.0), ), MIDDLE))

	#Mid sets
	M.parts['Part-1'].Set(name='mid-side', vertices=
	    M.parts['Part-1'].vertices.findAt(((0.0, 150.0, 1500.0), )))
	M.parts['Part-1'].Set(name='mid-back', vertices=
	    M.parts['Part-1'].vertices.findAt(((150.0, 0.0, 1500.0), )))
	M.parts['Part-1'].Set(name='mid-front', vertices=
	    M.parts['Part-1'].vertices.findAt(((-150.0, 0.0, 1500.0), )))


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
    	((-150.0, 1000.0,  50.0), ),
    	((-150.0, 2000.0, -50.0), ), ))
	M.rootAssembly.Surface(name='back', side1Faces=
	    M.rootAssembly.instances['Part-1-1'].faces.findAt(
	    ((150.0, 2000.0,  50.0), ),
	    ((150.0, 1000.0, -50.0), ), ))
	M.rootAssembly.Surface(name='sides', side1Faces=
	    M.rootAssembly.instances['Part-1-1'].faces.findAt(
	    ((-50.0,    0.0, -150.0), ), 
	    (( 50.0,    0.0,  150.0), ),
	    ((-50.0, 2000.0, -150.0), ),))
	# M.rootAssembly.Surface(name='smallPlate', side1Faces=
	# 	M.rootAssembly.instances['Part-2-1'].faces.findAt(
	# 	((-1000.0, 25.0, -25.0), )))

	#Join surfaces to blast surface
	M.rootAssembly.SurfaceByBoolean(name='blastSurf', 
	    surfaces=(
	    M.rootAssembly.surfaces['back'], 
	    M.rootAssembly.surfaces['sides'], 
	    M.rootAssembly.surfaces['front'],))
	

	#=========== Mesh  ============#
	M.parts['Part-1'].seedPart(deviationFactor=0.1, 
    minSizeFactor=0.1, size=seed)
	M.parts['Part-1'].generateMesh()
	

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



def pressureLoad(modelName, stepName, ampFile, surf):
	M=mdb.models[modelName]

	#Pressure amplitude from ampFile
	firstRow=1
	table=[]
	with open('inputData/'+ampFile, 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		for row in reader:
			if firstRow: 
				firstRow=0
			else:
				table.append((float(row[0]), float(row[1])))
				blastTime = float(row[0])
	tpl = tuple(table)
	M.TabularAmplitude(name='blast', timeSpan=STEP, 
	   	smooth=SOLVER_DEFAULT, data=(tpl))


	#Pressure load
	M.Pressure(name='Load-1', createStepName=stepName, 
	    region=M.rootAssembly.surfaces[surf], distributionType=UNIFORM,
	    field='', magnitude=1.0, amplitude='blast')









#=========== Post  ============#


def xyShell(modelName):
	'''
	Prints xy data for displacment at mid col, forces at top
	and force-displacemnt
	'''

	#Open ODB
	odb = func.open_odb(modelName)


	#=========== Displament at mid col  ============#
	
	#Get node numbers
	sideNodeNr=odb.rootAssembly.instances['PART-1-1'].\
		nodeSets['MID-SIDE'].nodes[0].label
	# backNodeNr=odb.rootAssembly.instances['PART-1-1'].\
	# 	nodeSets['MID-BACK'].nodes[0].label
	# frontNodeNr=odb.rootAssembly.instances['PART-1-1'].\
	# 	nodeSets['MID-FRONT'].nodes[0].label

	#Create output names
	sideName= 'Spatial displacement: U1 PI: PART-1-1 Node '+str(sideNodeNr)+\
		' in NSET MID-SIDE'
	# backName= 'Spatial displacement: U1 PI: PART-1-1 Node '+str(backNodeNr)+\
	# 	' in NSET MID-BACK'
	# frontName='Spatial displacement: U1 PI: PART-1-1 Node '+str(frontNodeNr)+\
	# 	' in NSET MID-FRONT'

	#Get xy data
	xyU1side = xyPlot.XYDataFromHistory(odb=odb,
		outputVariableName=sideName, name='U1midSide')
	# xyU1back = xyPlot.XYDataFromHistory(odb=odb,
	# 	outputVariableName=backName, name='U1midBack')
	# xyU1front = xyPlot.XYDataFromHistory(odb=odb,
	# 	outputVariableName=frontName, name='U1midFront')
		
	#Print to file
	func.XYplot(modelName, plotName = 'U1midSide',
		xHead='Time [s]', yHead='Displacement [mm]',
		xyDat= xyU1side)
	# func.XYplot(modelName, plotName = 'U1midBack',
	# 	xHead='Time [s]', yHead='Displacement [mm]',
	# 	xyDat= xyU1back)
	# func.XYplot(modelName, plotName = 'U1midFront',
	# 	xHead='Time [s]', yHead='Displacement [mm]',
	# 	xyDat= xyU1front)


	#=========== R2 at top and bot  ============#
	#Get node numbers
	topNodeNr =[]
	for nodes in odb.rootAssembly.instances['PART-1-1'].nodeSets['TOP'].nodes:
		topNodeNr.append(nodes.label)
	botNodeNr =[]
	for nodes in odb.rootAssembly.instances['PART-1-1'].nodeSets['BOT'].nodes:
		botNodeNr.append(nodes.label)

	#Create output names
	topNames = []
	for nr in topNodeNr:
		topNames.append('Reaction force: RF1 PI: PART-1-1 Node '
			+str(nr)+' in NSET TOP')
	botNames = []
	for nr in botNodeNr:
		botNames.append('Reaction force: RF1 PI: PART-1-1 Node '
			+str(nr)+' in NSET BOT')

	#Get xy data
	xyTopLst = []
	for name in topNames:
		xyTopLst.append(xyPlot.XYDataFromHistory(odb=odb, 
			outputVariableName=name))
	xyTopTup = tuple(xyTopLst)
	xyBotLst = []
	for name in botNames:
		xyBotLst.append(xyPlot.XYDataFromHistory(odb=odb, 
			outputVariableName=name))
	xyBotTup = tuple(xyBotLst)
	
	xyR1Top = sum(xyTopTup)
	xyR1Bot = sum(xyBotTup)
	xyR1Tot = sum(xyR1Top,xyR1Bot)

	#Print to file
	func.XYplot(modelName, plotName = 'R1top',
		xHead='Time [s]', yHead='Force [N]',
		xyDat= xyR1Top)
	func.XYplot(modelName, plotName = 'R1bot',
		xHead='Time [s]', yHead='Force [N]',
		xyDat= xyR1Bot)
	func.XYplot(modelName, plotName = 'R1',
		xHead='Time [s]', yHead='Force [N]',
		xyDat= xyR1Tot)


	#=========== Force Displacement  ============#
	xyRU = combine(xyU1side,-xyR1Tot)		
	func.XYplot(modelName, plotName = 'forceDisp',
		xHead='Displacment [mm]', yHead='Force [N]',
		xyDat= xyRU)
	







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
	func.fixReportFile(tempFile, plotName, modelName,
		x='Time [s]', y='Displacement [mm]')