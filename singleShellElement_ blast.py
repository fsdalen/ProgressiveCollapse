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
import csv
from datetime import datetime



#=======================================================#
#=======================================================#
#                   CONTROLS                            #
#=======================================================#
#=======================================================#

run = 1
stepTime = 0.05
distances = [01000,05000,10000]

#==========================================================#
#==========================================================#
#                   Perliminary                            #
#==========================================================#
#==========================================================#
#Own modules
from lib import func as func
reload(func)


#Makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,
	recoverGeometry=COORDINATE)
#Print begin script to console
print '\n'*6
print '###########    NEW SCRIPT    ###########'
print str(datetime.now())[:19]

modelName= 'deg00'
#Create model
mdb.Model(name=modelName, modelType=STANDARD_EXPLICIT)
#Delete all other models
func.delModels(modelName)

M=mdb.models[modelName]



#===========================================================#
#===========================================================#
#                   CREATE MODEL                            #
#===========================================================#
#===========================================================#


#=========== Part  ============#
#Material
M.Material(name='Material-1')
M.materials['Material-1'].Density(table=((1.0, ), ))
M.materials['Material-1'].Elastic(table=((1000.0, 
    0.3), ))

#Section
M.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
    integrationRule=SIMPSON, material='Material-1', name='Section-1', 
    numIntPts=5, poissonDefinition=DEFAULT, preIntegrate=OFF,
    thickness=1.0, thicknessField='', thicknessModulus=None, 
    thicknessType=UNIFORM, useDensity=OFF)

#Part
M.ConstrainedSketch(name='__profile__', sheetSize=200.0)
M.sketches['__profile__'].rectangle(point1=(-0.5, -0.5), 
    point2=(0.5, 0.5))
M.Part(dimensionality=THREE_D, name='Part-1', type=
    DEFORMABLE_BODY)
M.parts['Part-1'].BaseShell(sketch=
    M.sketches['__profile__'])
del M.sketches['__profile__']


#Assign section
M.parts['Part-1'].SectionAssignment(offset=0.0, 
    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
    faces=M.parts['Part-1'].faces.getSequenceFromMask(
    mask=('[#1 ]', ), )), sectionName='Section-1', thicknessAssignment=
    FROM_SECTION)

#Mesh
M.parts['Part-1'].seedPart(deviationFactor=0.1, 
    minSizeFactor=0.1, size=1.0)
M.parts['Part-1'].generateMesh()
M.rootAssembly.regenerate()

#Surface
M.parts['Part-1'].Surface(name='Surf-1', side2Faces=
    M.parts['Part-1'].faces.findAt(((-0.166667, 
    -0.166667, 0.0), )))

#Set
M.parts['Part-1'].Set(edges=
    M.parts['Part-1'].edges.findAt(((0.25, -0.5, 
    0.0), ), ((0.5, 0.25, 0.0), ), ((-0.25, 0.5, 0.0), ), ((-0.5, -0.25, 0.0), 
    ), ), name='edges')



#=========== Assembly  ============#
#Assembly
M.rootAssembly.DatumCsysByDefault(CARTESIAN)

names = ['ELEMENT'+str(dist) for dist in distances]

for name in names:
	M.rootAssembly.Instance(dependent=ON, name=name, 
    	part=M.parts['Part-1'])

	#Rotate
	M.rootAssembly.rotate(angle=90.0, axisDirection=(0.0, 1.0, 
		0.0), axisPoint=(0.0, 0.0, 0.0), instanceList=(name, ))
	
	#Tranlate
	dist = float(name[7:])
	M.rootAssembly.translate(instanceList=(name, ), 
		vector=(9000+dist, 0.0, 0.0))


#Merges sets
lst=[]
for name in names:
	lst.append(M.rootAssembly.allInstances[name].sets['edges'])
tup=tuple(lst)
M.rootAssembly.SetByBoolean(name='allEdges', sets=tup)


#Merges surfaces
lst=[]
for name in names:
	lst.append(M.rootAssembly.allInstances[name].surfaces['Surf-1'])
tup=tuple(lst)
M.rootAssembly.SurfaceByBoolean(name='blastSurf', surfaces=tup)


#=========== BC  ============#
region=M.rootAssembly.sets['allEdges']
M.DisplacementBC(name='BC-1', 
    createStepName='Initial', region=region, u1=SET, u2=SET, u3=SET, ur1=SET, 
    ur2=SET, ur3=SET, amplitude=UNSET, distributionType=UNIFORM, fieldName='', 
    localCsys=None)





#================================================================#
#================================================================#
#                   STEP DEPENDENCIES                            #
#================================================================#
#================================================================#

#=========== Step  ============#
M.ExplicitDynamicsStep(name='Step-1', 
    previous='Initial', timePeriod=stepTime, maxIncrement=0.0001)


#=========== Output  ============#

del M.fieldOutputRequests['F-Output-1']
M.FieldOutputRequest(name='F-Output-1', 
    createStepName='Step-1', variables=('U', 'UT', 'UR', 'V', 'VT', 'VR', 'A', 
    'AT', 'AR', 'RBANG', 'RBROT'))
del M.historyOutputRequests['H-Output-1']

M.HistoryOutputRequest(createStepName='Step-1', name=
    'R', rebar=EXCLUDE, region=
    M.rootAssembly.sets['allEdges'], sectionPoints=
    DEFAULT, variables=('RF1','RF2','RF3' ))


#=========== Conwep  ============#
func.addConWep(modelName, TNT=1, blastType=SURFACE_BLAST,
	coordinates=(0.0,0.0,0.0),timeOfBlast=0, stepName='Step-1')

#=========== Incident Wave  ============#
func.addIncidentWave(modelName, stepName='Step-1', AmpFile='blastAmp.txt',
	sourceCo=(0.0,0.0,0.0),
	refCo=(9000.0,0.0,0.0))
M.interactions['incidentWave'].suppress()





#===========================================================#
#===========================================================#
#                   RUN AND POST                            #
#===========================================================#
#===========================================================#

#Create 45 an 90 deg models
mdb.Model(name='deg45', objectToCopy=mdb.models['deg00'])
M=mdb.models['deg45']
for name in names:
	dist = float(name[7:])
	#Rotate
	M.rootAssembly.rotate(angle=45.0,
		axisPoint    =(9000+dist, 0.0, 0.0),
		axisDirection=(0, 1.0, 0.0),
		instanceList=(name, ))

mdb.Model(name='deg90', objectToCopy=mdb.models['deg00'])
M=mdb.models['deg90']
for name in names:
	dist = float(name[7:])
	#Rotate
	M.rootAssembly.rotate(angle=90.0,
		axisPoint    =(9000+dist, 0.0, 0.0),
		axisDirection=(0, 1.0, 0.0),
		instanceList=(name, ))


modelList = ['deg00', 'deg45', 'deg90']
#Save model
mdb.saveAs(pathName = 'singleElement' + '.cae')

for modelName in modelList:
	M=mdb.models[modelName]
	#ConWep
	M.rootAssembly.regenerate()
	mdb.Job(model=modelName, name=modelName+'conWep')
	if run:
		func.runJob(modelName+'conWep')
	#Incident wave
	M.interactions['conWep'].suppress()
	M.interactions['incidentWave'].resume()
	mdb.Job(model=modelName, name=modelName+'incidentWave')
	if run:
		func.runJob(modelName+'incidentWave')



#===================================================#
#===================================================#
#                   POST                            #
#===================================================#
#===================================================#

if run:
	print 'Post...'
	#Create list of jobs/odbs
	lst = [[model+'conWep', model+'incidentWave'] for model in modelList]
	jobLst = []
	map(jobLst.extend, lst)


	#Itterate over jobs
	#RF1
	for job in jobLst:
		odb = func.open_odb(job)
		#Create names of history outputs
		xyNames ={}
		for name in names:
			xyNames[name]= 'Reaction force: RF1 PI: '+name+' Node 1'
		#Get xy data
		xyDic = {}
		for name, xyName in xyNames.iteritems():
			xyDic[name] = xyPlot.XYDataFromHistory(odb=odb,
				outputVariableName=xyName)
		#Print xy data
		for name, xyDat in xyDic.iteritems():
			func.XYplot(modelName=job, plotName='RF1-'+name.lower(),
				xHead='Time [s]', yHead='Force [N]',
				xyDat=xyDat)
	#RF3
	for job in jobLst:
		odb = func.open_odb(job)
		#Create names of history outputs
		xyNames ={}
		for name in names:
			xyNames[name]= 'Reaction force: RF3 PI: '+name+' Node 1'
		#Get xy data
		xyDic = {}
		for name, xyName in xyNames.iteritems():
			xyDic[name] = xyPlot.XYDataFromHistory(odb=odb,
				outputVariableName=xyName)
		#Print xy data
		for name, xyDat in xyDic.iteritems():
			func.XYplot(modelName=job, plotName='RF3-'+name.lower(),
				xHead='Time [s]', yHead='Force [N]',
				xyDat=xyDat)

print '   done'


print '###########    END OF SCRIPT    ###########'