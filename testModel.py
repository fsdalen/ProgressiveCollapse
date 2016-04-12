from abaqus import *
from abaqusConstants import *
#====================================================================#
#====================================================================#
#						INPUTS										 #
#====================================================================#
#====================================================================#


run       =      0	     	#If 1: run job
saveModel =     0			#If 1: Save model
cpus      =   	1			#Number of CPU's
post      =   	0			#Run post prossesing
snurre    = 	0			#1 if running on snurre (removes extra commands like display ODB)

modelName = "testMod"
jobName   = 'damageJob'
stepName  = "damageStep"	

stepTime = 3.0
load     = 1.0e7
seed1    = 800.0

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

#Deletes all other models
if len(mdb.models.keys()) > 0:							
	a = mdb.models.items()
	for i in range(len(a)):
		b = a[i]
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
#Static step
#M.StaticStep(name='Step-1', previous='Initial', 
#    initialInc=0.1)

#Explicit Step
M.ExplicitDynamicsStep(name='Step-1', previous='Initial', 
    timePeriod=stepTime)

#================ BC ==================#
region = M.rootAssembly.instances['COLUMN-1'].sets['col-base']
M.DisplacementBC(name='BC-1', createStepName='Initial', 
    region=region, u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET, 
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)


#================ Load ==================#
region = M.rootAssembly.instances['COLUMN-1'].sets['col-top']
M.ConcentratedForce(name='Load-1', createStepName='Step-1', 
    region=region, cf2=load, distributionType=UNIFORM, field='', 
    localCsys=None)
                    


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

#====================================================================#
#====================================================================#
#                        Incident wave                               #
#====================================================================#
#====================================================================#

if 0:
    fluidDensity = 1.225e-12    #1.225 kg/m^3
    soundSpeed =340.29e3    # 340.29 m/s

    #Create interaction property
    M.IncidentWaveProperty(name='Blast', 
        definition=SPHERICAL, fluidDensity=fluidDensity, soundSpeed=soundSpeed)

    #Source Point
    M.rootAssembly.ReferencePoint(point=(-1000.0, 2000.0, 0.0))

    #Reference Point
    M.rootAssembly.ReferencePoint(point=(-500.0, 2000.0, 0.0))


    #Pressure amplitude
    M.TabularAmplitude(name='Blast', timeSpan=STEP, 
        smooth=SOLVER_DEFAULT, data=((0.0, 0.0), (0.01, 1000.0), (0.1, 0.0)))

    a = mdb.models['testMod'].rootAssembly
    r1 = M.rootAssembly.referencePoints
    refPoints1=(r1[4], )
    region1=a.Set(referencePoints=refPoints1, name='m_Set-1')
    a = mdb.models['testMod'].rootAssembly
    r1 = a.referencePoints
    refPoints1=(r1[5], )
    region2=a.Set(referencePoints=refPoints1, name='Set-1')
    a = mdb.models['testMod'].rootAssembly
    c1 = a.instances['COLUMN-1'].edges
    circumEdges1 = c1.findAt(((0.0, 1000.0, 0.0), ))
    region3=a.Surface(circumEdges=circumEdges1, name='s_Surf-1')
    mdb.models['testMod'].IncidentWave(name='Int-1', createStepName='Step-1', 
        sourcePoint=region1, standoffPoint=region2, surface=region3, 
        definition=PRESSURE, interactionProperty='Blast', 
        referenceMagnitude=1000.0, amplitude='Amp-1', imaginaryAmplitude='')



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

