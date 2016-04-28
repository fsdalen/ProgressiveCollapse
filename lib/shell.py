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
#from caeModules import *

# HUP 300x300
# HEB 550 beam








#====================================================#
#====================================================#
#                   Blast                            #
#====================================================#
#====================================================#

def conWep(modelName, TNT, blastType, coordinates, stepName):
	'''
	blastType = AIR_BLAST SURFACE_BLAST
	name of surf must be blastSurf
	'''
	M=mdb.models[modelName]

	#Create interaction property
	M.IncidentWaveProperty(definition= blastType,
	    massTNT=TNT, massFactor=1.0e3,
	    lengthFactor=1.0e-3, pressureFactor=1.0e6,
	    name='IntProp-1',)

	#Source Point
	feature = M.rootAssembly.ReferencePoint(point=coordinates)
	ID = feature.id
	sourceRP = M.rootAssembly.referencePoints[ID]
	M.rootAssembly.Set(name='Source', referencePoints=(sourceRP,))
	
	

	#Create ineraction
	M.IncidentWave(createStepName=stepName, definition=CONWEP, 
	    detonationTime=0.0, interactionProperty='IntProp-1',
	 	name='Int-1',
	    sourcePoint=M.rootAssembly.sets['Source'], 
	    surface=M.rootAssembly.surfaces['blastSurf'])
























#===========================================================#
#===========================================================#
#                   Simple blast                            #
#===========================================================#
#===========================================================#

def createSingleBeam(modelName, steel):
	# HUP 300x300
	M=mdb.models[modelName]


	thickness=10.0 	#Thickness of section
	width=300.0-thickness
	hight= 4200.0


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
		-48.333333, 2666.666667), (-1.0, 0.0, 0.0)), ((-48.333333, 145.0, 
		2666.666667), (0.0, 1.0, 0.0)), ((145.0, 48.333333, 2666.666667),
		(1.0, 0.0, 0.0)), ((48.333333, -145.0, 2666.666667),
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
	    ((-145.0, -72.5, 4200.0), ),
	    ((-72.5, 145.0, 4200.0), ),
	    ((145.0, 72.5, 4200.0), ),
	    ((72.5, -145.0, 4200.0), ), ),
	    name='top')



	#=========== Assembly  ============#
	M.rootAssembly.Instance(dependent=ON, name='Part-1-1',
		part=M.parts['Part-1'])
	M.rootAssembly.rotate(angle=-90.0,
		axisDirection=(1.0, 0.0, 0.0), axisPoint=(0.0, 0.0, 0.0),
		instanceList=('Part-1-1', ))

	#Create blast surface
	M.rootAssembly.Surface(name='blastSurf', side1Faces=
	    M.rootAssembly.instances['Part-1-1'].faces.findAt(((
	    -145.0, 2666.666667, 48.333333), ),
	    ((-48.333333, 2666.666667, -145.0), ), 
	    ((145.0, 2666.666667, -48.333333), ),
	    ((48.333333, 2666.666667, 145.0), ), 
	    ))


	#=========== Mesh  ============#
	seed = 300.0
	M.parts['Part-1'].seedPart(deviationFactor=0.1, 
    minSizeFactor=0.1, size=seed)
	M.parts['Part-1'].generateMesh()
	
	#Create set for mid node
	nodes = M.parts['Part-1'].nodes[53:54]
	M.parts['Part-1'].Set(nodes = nodes, name = 'midNode')

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






def xySimpleDef(modelName, printFormat):

	plotName = 'midU1'


	#Open ODB
	odb = func.open_odb(modelName)


	varName = 'Spatial displacement: U1 PI: PART-1-1 Node 54 in NSET MIDNODE'
	xy1 = xyPlot.XYDataFromHistory(odb=odb, 
    outputVariableName=varName)
	c1 = session.Curve(xyData=xy1)

	#Plot and Print
	func.XYprint(modelName, plotName, printFormat, c1)

	#Report data
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy1, ))
	func.fixReportFile(tempFile, plotName, modelName)



