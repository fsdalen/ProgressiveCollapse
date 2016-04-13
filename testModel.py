from abaqus import *
from abaqusConstants import *
#====================================================================#
#====================================================================#
#						INPUTS										 #
#====================================================================#
#====================================================================#


run       =     0	     	#If 1: run job
saveModel =     0			#If 1: Save model
cpus      =   	1			#Number of CPU's
post      =   	1			#Run post prossesing
snurre    = 	0			#1 if running on snurre (removes extra commands like display ODB)
blast     =     0

modelName = "testMod"
jobName   = 'damageJob'
stepName  = "damageStep"	

stepTime = 2.0
load     = 5.0e6
seed1    = 400.0

printFormat = PNG

#====================================================================#
#====================================================================#
#						PRELIMINARIES								 #
#====================================================================#
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
import odbAccess        		# To make ODB-commands available to the script
import xyPlot
import regionToolset

import odbFunc


#Print status to console during analysis
#import simpleMonitor
#if not snurre:
	#simpleMonitor.printStatus(ON)

#This makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,recoverGeometry=COORDINATE)



#================ Model ==================#

#Import model from mat input file
matFile = 'mat_1.inp'
mat1 = "DOMEX_S355"		#Material name
print '\n'*2
mdb.ModelFromInputFile(name=modelName, inputFileName=matFile)
print '\n'*2

		
M = mdb.models[modelName]
a = M.rootAssembly

#Deletes all other models
if len(mdb.models.keys()) > 0:							
	items = mdb.models.items()
	for i in range(len(items)):
		b = items[i]
		if b[0] != modelName:
			del mdb.models[b[0]]



#====================================================================#
#====================================================================#
#                       Create model                                 #
#====================================================================#
#====================================================================#

#================ Part ==================#

part1 = "COLUMN"
sect1 = "HUP"
col1_height = 4000.0

#Create Section and profile
M.BoxProfile(a=300.0, b=300.0, name='Profile-1', t1=10.0, uniformThickness=ON)
M.BeamSection(consistentMassMatrix=False, integration=
    DURING_ANALYSIS, material=mat1, name=sect1, poissonRatio=0.3, 
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
    point=p.InterestingPoint(edge=e.findAt(coordinates=(0.0, 1000.0, 0.0)), 
    rule=MIDDLE))

#Create set at middle
p = M.parts['COLUMN']
v = p.vertices
verts = v.findAt(((0.0, 2000.0, 0.0), ))
p.Set(vertices=verts, name='col-mid')

#================ Mesh ==================#
analysisType = STANDARD  #Could be STANDARD or EXPLICIT
element1 = B31 #B31 or B32 for linear or quadratic

#Seed
M.parts[part1].seedPart(minSizeFactor=0.1, size=seed1)

#Change element type
M.parts[part1].setElementType(elemTypes=(ElemType(
	elemCode=element1, elemLibrary=analysisType), ), regions=(
	M.parts[part1].edges.findAt((0.0, 0.0, 0.0), ), ))

#Mesh
M.parts[part1].generateMesh()


#================ Instance ==================#
M.rootAssembly.Instance(name='COLUMN-1', part=M.parts['COLUMN'], dependent=ON)


#================ Step ==================#
oldStep = 'Initial'
#Static step
#M.StaticStep(name=stepName, previous=oldStep, 
#    initialInc=0.1)

#Explicit Step
M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=stepTime)

#================ BC ==================#
region = M.rootAssembly.instances['COLUMN-1'].sets['col-base']
M.DisplacementBC(name='BC-1', createStepName='Initial', 
    region=region, u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET, 
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)

region = M.rootAssembly.instances['COLUMN-1'].sets['col-top']
M.DisplacementBC(name='BC-2', createStepName='Initial', 
    region=region, u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET, 
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)


#================ Load ==================#
M.SmoothStepAmplitude(name='Smooth', timeSpan=STEP, data=((
    0.0, 0.0), (1.0, 1.0)))

e1 = a.instances['COLUMN-1'].edges
edges1 = e1.findAt(((0.0, 1000.0, 0.0), ))
region = a.Set(edges=edges1, name='Set-1')
M.LineLoad(name='Load-2', createStepName=stepName, 
    region=region, comp1=5000.0, amplitude='Smooth')

# region = M.rootAssembly.instances['COLUMN-1'].sets['col-top']
# M.ConcentratedForce(name='Load-1', createStepName=stepName, 
#     region=region, cf2=load, distributionType=UNIFORM, field='', 
#     localCsys=None, amplitude='Smooth')
                    

#Field output
M.FieldOutputRequest(name='damage', 
    createStepName=stepName, variables=('SDEG', 'DMICRT', 'STATUS'))

#History output

regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-base']
M.HistoryOutputRequest(name='load-base', 
    createStepName='damageStep', variables=('RF1', ), region=regionDef, 
    sectionPoints=DEFAULT, rebar=EXCLUDE)

regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-top']
M.HistoryOutputRequest(name='load-top', 
    createStepName='damageStep', variables=('RF1', ), region=regionDef, 
    sectionPoints=DEFAULT, rebar=EXCLUDE)

regionDef=M.rootAssembly.allInstances['COLUMN-1'].sets['col-mid']
M.HistoryOutputRequest(name='displacement', 
    createStepName='damageStep', variables=('U1', ), region=regionDef, 
    sectionPoints=DEFAULT, rebar=EXCLUDE)


#====================================================================#
#====================================================================#
#                       Job and Post                                 #
#====================================================================#
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

mdb.Job(model=modelName, name=jobName, numCpus=cpus, numDomains=cpus)


def runJob(jobName):
    print 'Running %s...' %jobName
    try:
        mdb.jobs[jobName].submit(consistencyChecking=OFF)   #Run job
        mdb.jobs[jobName].waitForCompletion()
        dispJob()
    except:
        print mdb.jobs[jobName].status

if run:    
    runJob(jobName)

if post:
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


#Plot force-displacement
odb = session.odbs[jobName+'.odb']
rf1 = session.XYDataFromHistory(name='XYData-1', odb=odb, 
    outputVariableName='Reaction force: RF1 at Node 1 in NSET COL-BASE', )
# rf1 = session.XYDataFromHistory(name='XYData-2', odb=odb, 
#     outputVariableName='Reaction force: RF1 at Node 1 in NSET COL-BASE', )
rf2 = session.XYDataFromHistory(name='XYData-2', odb=odb, 
    outputVariableName='Reaction force: RF1 at Node 3 in NSET COL-TOP', )
# rf2 = session.XYDataFromHistory(name='XYData-3', odb=odb, 
#     outputVariableName='Reaction force: RF1 at Node 11 in NSET COL-TOP', )
u = session.XYDataFromHistory(name='XYData-3', odb=odb, 
    outputVariableName='Spatial displacement: U1 at Node 2 in NSET COL-MID', )
xy = combine(u, -(rf1+rf2))
c1 = session.Curve(xyData=xy)
plotName = 'force-displacement'
XYprint(jobName, plotName, printFormat, c1)



#====================================================================#
#====================================================================#
#                        Incident wave                               #
#====================================================================#
#====================================================================#

if blast:
    a = M.rootAssembly

    airDensity = 1.225e-12    #1.225 kg/m^3
    soundSpeed =340.29e3    # 340.29 m/s


    #Pressure amplitude
    M.TabularAmplitude(name='Blast', timeSpan=STEP, 
        smooth=SOLVER_DEFAULT, data=((0.0, 0.0), (0.1, 1.0), (1, 0.0)))

    #Source Point
    feature = a.ReferencePoint(point=(-1000.0, 2000.0, 0.0))
    ID = feature.id
    sourceRP = a.referencePoints[ID]
    a.Set(name='Source', referencePoints=(sourceRP,))

    #Standoff Point
    feature = a.ReferencePoint(point=(-500.0, 2000.0, 0.0))
    ID = feature.id
    standoffRP = a.referencePoints[ID]
    a.Set(name='Standoff', referencePoints=(standoffRP,))

    #Create surfaces to apply loads to
    circumEdges1 = a.instances['COLUMN-1'].edges.findAt(((0.0, 1000.0, 0.0), ))
    region3=a.Surface(circumEdges=circumEdges1, name='Column_surf')

    #Create interaction property
    M.IncidentWaveProperty(name='Blast', 
        definition=SPHERICAL, fluidDensity=airDensity, soundSpeed=soundSpeed)

    #Create incident Wave Interaction
    M.IncidentWave(name='Blast', createStepName=stepName, 
        sourcePoint=a.sets['Source'], standoffPoint=a.sets['Standoff'],
        surface=a.surfaces['Column_surf'],
        definition=PRESSURE, interactionProperty='Blast', 
        referenceMagnitude=1.0, amplitude='Blast')

    #Fluid inertia of section
    M.sections['HUP'].setValues(useFluidInertia=ON, fluidMassDensity=airDensity, crossSectionRadius=300.0, 
        lateralMassCoef=1.15)   #latteralMassCoef is for rectangle from wikipedia

    #Set model wave formulation (does not matter when fluid is not modeled)
    M.setValues(waveFormulation=TOTAL)

    #New step
    freeTime = 2.0
    oldStep = stepName
    stepName = 'freeStep'
    M.ExplicitDynamicsStep(name=stepName, previous=oldStep, 
    timePeriod=freeTime)

    # runJob(jobName)

    #  Blast history
    #  
    #    Get a master thesis from David

    #  Beam fluid inertia
    #  
    #      Drag coefficients
    #      Air density

    #  Propagation of wave
    #  
    #      Default is Accustic (1/R)
#"Bounce" surface?

