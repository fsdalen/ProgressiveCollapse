#Abaqus modules
from abaqus import *
from abaqusConstants import *
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *

#My modules
from lib import func as func


#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#


modelName = 'ConWepPressure'
run       = 1
TNT       = 1.0 	#(tonn)
standoff  = 9000.0
intervals = 1000
blastType = SURFACE_BLAST	#AIR_BLAST or SURFACE_BLAST




#==========================================================#
#==========================================================#
#                   PERLIMINARY                            #
#==========================================================#
#==========================================================#
Mdb()
mdb.models.changeKey(fromName='Model-1', toName=modelName)
func.delModels(modelName)
M=mdb.models[modelName]

#Makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,
	recoverGeometry=COORDINATE)








#===========================================================#
#===========================================================#
#                   CREATE MODEL                            #
#===========================================================#
#===========================================================#

#Dummy material
M.Material(name='Mat')
M.materials['Mat'].Elastic(table=((200000.0, 
    0.3), ))


#Dummp part
M.ConstrainedSketch(name='__profile__', sheetSize=200.0)
M.sketches['__profile__'].rectangle(point1=(-1.0, -1.0), 
    point2=(1.0, 1.0))
M.Part(dimensionality=THREE_D, name='Part-1', type=
    DEFORMABLE_BODY)
M.parts['Part-1'].BaseSolidExtrude(depth=2.0, sketch=
    M.sketches['__profile__'])
del M.sketches['__profile__']
M.HomogeneousSolidSection(material='Mat',
	name='Section-1', thickness=None)
M.parts['Part-1'].SectionAssignment(offset=0.0, 
    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
    cells=M.parts['Part-1'].cells.findAt(((1.0, 
    0.333333, 1.333333), ), )), sectionName='Section-1', thicknessAssignment=
    FROM_SECTION)


#Mesh
M.parts['Part-1'].seedPart(deviationFactor=0.1, 
    minSizeFactor=0.1, size=20.0)
M.parts['Part-1'].generateMesh()

#Assemby
M.rootAssembly.Instance(dependent=ON, name=
    'Part-1-1', part=M.parts['Part-1'])

#Face sets
M.rootAssembly.Set(faces=
    M.rootAssembly.instances['Part-1-1'].faces.findAt(
    ((1.0, 0.333333, 1.333333), )), name='front')
M.rootAssembly.Set(faces=
    M.rootAssembly.instances['Part-1-1'].faces.findAt(
    ((-0.333333, -0.333333, 0.0), )), name='side')


#BlastSurf
M.rootAssembly.Surface(name='blastSurf', side1Faces=
    M.rootAssembly.instances['Part-1-1'].faces.findAt(
    ((-1.0, -0.333333, 1.333333), ), ((-0.333333, 1.0, 1.333333), ), ((1.0, 
    0.333333, 1.333333), ), ((0.333333, -1.0, 1.333333), ), ((-0.333333, 
    -0.333333, 2.0), ), ((0.333333, -0.333333, 0.0), ), ))

#BCs
M.DisplacementBC(amplitude=UNSET, createStepName=
    'Initial', distributionType=UNIFORM, fieldName='', localCsys=None, name=
    'BC-1', region=Region(
    vertices=M.rootAssembly.instances['Part-1-1'].vertices.findAt(
    ((-1.0, -1.0, 2.0), ),
    ((-1.0, 1.0, 2.0), ),
    ((-1.0, 1.0, 0.0), ),
    ((-1.0, -1.0, 0.0), ),
    ((1.0, 1.0, 2.0), ),
    ((1.0, 1.0, 0.0), ),
    ((1.0,  -1.0, 2.0), ),
    ((1.0, -1.0, 0.0), ), )),
    u1=SET, u2=SET, u3=SET, ur1=SET, 
    ur2=SET, ur3=SET)


#=========== Step  ============#
stepName = 'blast'
M.ExplicitDynamicsStep(name=stepName, previous=
    'Initial', timePeriod=0.01)



#=========== Output  ============#
del M.historyOutputRequests['H-Output-1']
del M.fieldOutputRequests['F-Output-1']
M.FieldOutputRequest(createStepName=stepName, name=
    'F-Output-1', numIntervals=intervals, region=
    M.rootAssembly.sets['front'],
    variables=('IWCONWEP', ))
M.FieldOutputRequest(createStepName=stepName, name=
    'F-Output-1', numIntervals=intervals, region=
    M.rootAssembly.sets['side'],
    variables=('IWCONWEP', ))


#=========== Load  ============#
func.addConWep(modelName, TNT, blastType,
	coordinates=(standoff,0,0), timeOfBlast=0, stepName=stepName)

#=========== Run  ============#
M.rootAssembly.regenerate()
#Save model
mdb.saveAs(pathName = mdbName + '.cae')

#Create job
mdb.Job(model=modelName, name=modelName,
	    numCpus=cpus, numDomains=cpus,
	    explicitPrecision=precision, nodalOutputPrecision=nodalOpt)

#Run job
if run:
	func.runJob(modelName)

#=========== Post  ============#
