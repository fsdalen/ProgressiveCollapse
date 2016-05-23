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


def createShellmod(modelName, x, z, y, seed, slabSeedFactor):
	'''
	Builds a shell model without step
	'''

	col_height = 3000.0
	beam_len   = 7500.0

	M=mdb.models[modelName]

	steel = 'DOMEX_S355'
	concrete = 'Concrete'
	rebarSteel = steel


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

	# Add rebars to section (both directions)
	M.sections['SLAB'].RebarLayers(layerTable=(
	    LayerProperties(barArea=rebarArea, orientationAngle=0.0,
	    barSpacing=rebarSpacing, layerPosition=rebarPosition,
	    layerName='Layer 1', material=rebarSteel),
	    LayerProperties(barArea=rebarArea, orientationAngle=90.0,
	    barSpacing=rebarSpacing, layerPosition=rebarPosition,
	    layerName='Layer 2', material=rebarSteel)
	    ),  
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
	M.parts['COLUMN'].Surface(name='column', side1Faces=
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
	gap = 0
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
		if not key.startswith('SLAB'):
			instLst.append(M.rootAssembly.instances[key])
	instTup	= tuple(instLst)
	M.rootAssembly.InstanceFromBooleanMerge(domain=GEOMETRY
	    , instances=instTup, name='FRAME'
	    , originalInstances=DELETE,
	    keepIntersections=ON)



	#=========== Connect slabs to beams  ============#

	#Beam s
	frame = M.rootAssembly.instances['FRAME-1']
	count=0
	for a in range(x-1):
		for n in range(z-1):
			for etg in range(y):
				count = count+1
				setName = 'beamEdges-'+str(count)

				edge1 = frame.edges.findAt(((
					beam_len  *     a  + 200,
					col_height*(etg+1) + 150,
					beam_len  *     n  +   0),),)
				edge2 = frame.edges.findAt(((
					beam_len  *     a  + 200,
					col_height*(etg+1) + 150,
					beam_len  *  (n+1) +   0),),)

				M.rootAssembly.Set(edges=
					edge1 + edge2, name=setName)


	count=0
	for a in range(x-1):
		for n in range(z-1):
			for etg in range(y):
				count = count+1
				instName = 'SLAB-'+str(count)
				inst=M.rootAssembly.instances[instName]
				setName = 'slabEdges-'+str(count)

				edge1 = inst.edges.findAt(((
					beam_len  *     a  + 200,
					col_height*(etg+1) + 150,
					beam_len  *     n  +   0),),)
				edge2 = inst.edges.findAt(((
					beam_len  *     a  + 200,
					col_height*(etg+1) + 150,
					beam_len  *  (n+1) +   0),),)

				M.rootAssembly.Surface(side1Edges=
					edge1 + edge2, name=setName)

	
	for num in range(count):
		M.Tie(adjust=ON, name='tie-'+str(num+1), tieRotations=OFF,
			master= M.rootAssembly.sets['beamEdges-'+str(num+1)],
			slave= M.rootAssembly.surfaces['slabEdges-'+str(num+1)], 
			positionToleranceMethod=COMPUTED,  thickness=OFF)





	#=========== Create blast surface  ============#
	#Create blast surf
	lst=[]
	lst.append(M.rootAssembly.allInstances['FRAME-1'].surfaces['beam'])
	lst.append(M.rootAssembly.allInstances['FRAME-1'].surfaces['column'])
	for num in range((x-1)*(z-1)*y):
		lst.append(
			M.rootAssembly.instances['SLAB-'+str(num+1)].surfaces['topSurf'])
		lst.append(
			M.rootAssembly.instances['SLAB-'+str(num+1)].surfaces['botSurf'])
	tup=tuple(lst)
	M.rootAssembly.SurfaceByBoolean(name='blastSurf', 
	    surfaces=tup)
	



	#=========== Mesh  ============#
	M.parts['FRAME'].seedPart(deviationFactor=0.1, 
	    minSizeFactor=0.1, size=seed)
	M.parts['FRAME'].generateMesh()
	M.parts['SLAB'].seedPart(deviationFactor=0.1, 
	    minSizeFactor=0.1, size=seed*slabSeedFactor)
	M.parts['SLAB'].generateMesh()

	#Write nr of elements to results file
	nrElm = len(M.parts['FRAME'].elements)
	with open('results.txt', 'a') as f:
		f.write("%s	Elements: %s \n" %(modelName, nrElm))




	#=========== BC  ============#
	#Fix column feet
	M.DisplacementBC(amplitude=UNSET, createStepName=
		'Initial', distributionType=UNIFORM, fieldName='',
		localCsys=None, name='BC-1', 
		region=M.rootAssembly.sets['FRAME-1.colBot'],
		u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET)








#======================================================#
#======================================================#
#                   LOADING                            #
#======================================================#
#======================================================#

#=========== Live load  ============#
def surfaceTraction(modelName, stepName, x,z,y, load, amp=UNSET):
	'''
	Adds a surface traction to all slabs in the shell model

	ModelName = name of model
	Load      = magnitude of traciton
	x,z,y     = size of building
	'''
	M =mdb.models[modelName]
	for num in range((x-1)*(z-1)*y):
		reg = M.rootAssembly.instances['SLAB-'+str(num+1)].surfaces['topSurf']
		M.SurfaceTraction(createStepName=stepName, 
			directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
			distributionType=UNIFORM, follower=OFF, magnitude= load,
			name="LL-"+str(num+1), region=reg, traction=GENERAL, amplitude=amp)










#===================================================#
#===================================================#
#                   POST                            #
#===================================================#
#===================================================#




def xyR2colBase(modelName, x,z):

	odb=func.open_odb(modelName)
	 	
	steps = tuple(odb.steps.keys())
	lst=[]

	nodeLst = []
	for node in odb.rootAssembly.instances['FRAME-1'].nodeSets['COLBOT'].nodes:
		nodeLst.append(node.label)

	for nodeNr in nodeLst:
		varName='Reaction force: RF2 PI: FRAME-1 Node '+str(nodeNr)+\
			' in NSET COLBOT'
		lst.append(xyPlot.XYDataFromHistory(odb=odb, 
		    outputVariableName=varName, steps=steps, ))

	tpl=tuple(lst)
	xyR2 = sum(tpl)

	func.XYplot(modelName,
		plotName='R2colBase',
		xHead='Time [s]', yHead='Force [N]',
		xyDat=xyR2)

	return xyR2




def xyCenterU2_colBaseR2(modelName,x,z):
	odb=func.open_odb(modelName)


	#=========== R2 at column base  ============#
	xyR2 = xyR2colBase(modelName, x,z)

	#=========== U2 at center slab  ============#
	xyU2 = xyPlot.XYDataFromHistory(odb=odb, outputVariableName=
		'Spatial displacement: U2 PI: SLAB-1 Node 25 in NSET CENTERSLAB', )
	func.XYplot(modelName,
		plotName='U2centerSlab',
		xHead='Time [s]', yHead='Displacement [mm]',
		xyDat=xyU2)

	#=========== Force-Displacement  ============#
	xyRD = combine(-xyU2,xyR2)
	func.XYplot(modelName,
		plotName='forceDisp',
		xHead='Displacement [mm]', yHead='Force [N]', 
		xyDat=xyRD)	
	