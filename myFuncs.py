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
from datetime import datetime
import csv




#===============================================================#
#===============================================================#
#                   PERLIMINARY		                            #
#===============================================================#
#===============================================================#



#=========== Simple monitor  ============#
"""
simpleMonitor.py

Print status messages issued during an ABAQUS solver 
analysis to the ABAQUS/CAE command line interface
"""
def simpleCB(jobName, messageType, data, userData):
	"""
	This callback prints out all the
	members of the data objects
	"""
	format = '%-18s  %-18s  %s'
	print '\n'*2	
	print 'Message type: %s'%(messageType)
	members =  dir(data)
	for member in members:
		if member.startswith('__'): continue # ignore "magic" attrs
		memberValue = getattr(data, member)
		memberType = type(memberValue).__name__
		print format%(member, memberType, memberValue)
def printStatus(start=ON):
    """
    Switch message printing ON or OFF
    """
    
    if start:
        monitorManager.addMessageCallback(ANY_JOB, 
            STATUS, simpleCB, None)
    else:
        monitorManager.removeMessageCallback(ANY_JOB, 
            ANY_MESSAGE_TYPE, simpleCB, None)




#=========== Model functions  ============#

def delModels(modelName):    
	"""
	Deletes all models but modelName

	modelName= name of model to keep
	"""
	if len(mdb.models.keys()) > 0:							
		a = mdb.models.items()
	for i in range(len(a)):
		b = a[i]
		if b[0] != modelName:
			del mdb.models[b[0]]

def delJobs(exeption):
	"""
	-Closes open odb files
	-Deletes jobs
	-Deletes .odb and .imp files
		(Because runnig Abaqus in Parallels often creates
		corrupted files)

	exeption = .inp file not to delete 
	"""
	#Close and delete odb files
	fls = glob.glob('*.odb')
	for i in fls:
		if len(session.odbs.keys())>0:
			session.odbs[i].close()
		os.remove(i)
	#Delete old input files
	inpt = glob.glob('*.inp')
	for i in inpt:
		if not i == exeption:
			os.remove(i)
	#Delete old jobs
	jbs = mdb.jobs.keys()
	if len(jbs)> 0:
		for i in jbs:
			del mdb.jobs[i]
	print 'Old jobs and ODBs have been closed.'




#==========================================================#
#==========================================================#
#                   Build model                            #
#==========================================================#
#==========================================================#


def createMaterials(M, mat1, mat2, mat3):
	'''
	Adds damping to imported steel model
	Creates concrete and rebar steel

	M: model
	mat1, mat2, mat3: Name of materials
	'''

	damping = 0.05	#Mass proportional damping, same for all materials

	# Concrete
	mat2_Description = 'Elastic-perfect plastic'
	mat2_dens = 2.5e-09		#Density
	mat2_E = 35000.0		#E-module
	mat2_v = 0.3			#Poisson
	mat2_yield = 30.0			#Yield stress

	# Reebar steel
	mat3_Description = 'Elastic-linear plastic (rather random hardening)'
	mat3_dens = 8.0e-09		#Density
	mat3_E = 210000.0		#E-module
	mat3_v = 0.3			#Poisson
	mat3_yield = 355.0		#Yield stress




	#=========== Steel  ============#
	#Steel is already imported but needs damping
	M.materials[mat1].Damping(alpha=damping)

	#================ Concrete ==================#
	M.Material(description=mat2_Description, name=mat2)
	M.materials[mat2].Density(table=((mat2_dens, ), ))
	M.materials[mat2].Elastic(table=((mat2_E, mat2_v), ))
	M.materials[mat2].Plastic(table=((mat2_yield, 0.0), ))
	M.materials[mat2].Damping(alpha=damping)

	#================ Rebar Steel ==================#
	M.Material(description=mat3_Description, name=mat3)
	M.materials[mat3].Density(table=((mat3_dens, ), ))
	M.materials[mat3].Elastic(table=((mat3_E, mat3_v), ))
	M.materials[mat3].Plastic(table=((mat3_yield, 0.0), ))
	M.materials[mat3].Damping(alpha=damping)
	M.materials[mat3].plastic.setValues(table=((355.0, 
	    0.0), (2000.0, 20.0)))
	



def createColumn(M, height, mat, partName):
	'''
	Creates a RHS 300x300 column

	M: 		model
	height: height of column
	mat:    material
	'''
	
	sectName = "HUP300x300"

	#Create section and profile
	M.BoxProfile(a=300.0, b=300.0, name='Profile-1', t1=10.0, uniformThickness=ON)
	M.BeamSection(consistentMassMatrix=False, integration=
	    DURING_ANALYSIS, material=mat, name=sectName, poissonRatio=0.3, 
	    profile='Profile-1', temperatureVar=LINEAR)

	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize=20.0)
	M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(0.0, height))
	M.Part(dimensionality=THREE_D, name=partName, type=DEFORMABLE_BODY)
	M.parts[partName].BaseWire(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']

	#Assign section
	M.parts[partName].SectionAssignment(offset=0.0, 
	    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 
	    0.0), ), )), sectionName=sectName, thicknessAssignment=FROM_SECTION)

	#Assign beam orientation
	M.parts[partName].assignBeamSectionOrientation(method=
	    N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 0.0), ), )))




def createBeam(M, length, mat, partName):
	'''
	Creates a HEB 550 beam

	M:		 model
	length:  lenght of beam
	mat:	 material
	'''
	
	sectName = "HEB550"

	#Create Section and profile
	#HEB 550
	M.IProfile(b1=300.0, b2=300.0, h=550.0, l=275.0, name=
	    'Profile-2', t1=29.0, t2=29.0, t3=15.0)	#Now IPE profile, see ABAQUS for geometry definitions

	M.BeamSection(consistentMassMatrix=False, integration=
	    DURING_ANALYSIS, material=mat, name=sectName, poissonRatio=0.3, 
	    profile='Profile-2', temperatureVar=LINEAR)

	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize=10000.0)
	M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(length, 0.0))
	M.Part(dimensionality=THREE_D, name=partName, type=DEFORMABLE_BODY)
	M.parts[partName].BaseWire(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']

	#Assign section
	M.parts[partName].SectionAssignment(offset=0.0, 
	    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 
	    0.0), ), )), sectionName=sectName, thicknessAssignment=FROM_SECTION)

	#Assign beam orientation
	M.parts[partName].assignBeamSectionOrientation(method=
	    N1_COSINES, n1=(0.0, 0.0, -1.0), region=Region(
	    edges=M.parts[partName].edges.findAt(((0.0, 0.0, 0.0), ), )))




def createSlab(M, t, mat, dim, rebarMat, partName):
	'''
	Creates a square slab with thickness 200.0

	M:	      Model
	t:	  	  Thickness of slab
	mat:  	  Material of section
	dim:	  Dimention of square
	rebarMat: Material of rebars
	'''

	sectName = "Slab"

	rebarDim = 20.0			#mm^2 diameter
	rebarArea = 3.1415*(rebarDim/2.0)**2		#mm^2
	rebarSpacing = 120.0		#mm
	rebarPosition = -80.0		#mm distance from center of section

	#Create Section
	M.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
	    integrationRule=SIMPSON, material=mat, name=sectName, numIntPts=5, 
	    poissonDefinition=DEFAULT, preIntegrate=OFF,
	    temperature=GRADIENT, thickness=t, thicknessField='',
	    thicknessModulus=None, thicknessType=UNIFORM, useDensity=OFF)

	#Add rebars to section
	M.sections[sectName].RebarLayers(layerTable=(
	    LayerProperties(barArea=rebarArea, orientationAngle=0.0,
	    barSpacing=rebarSpacing, layerPosition=rebarPosition,
	    layerName='Layer 1', material=rebarMat), ), 
	    rebarSpacing=CONSTANT)	
		
	#Create part
	M.ConstrainedSketch(name='__profile__', sheetSize= 10000.0)
	M.sketches['__profile__'].rectangle(point1=(0.0, 0.0),
		point2=(dim, dim))
	M.Part(dimensionality=THREE_D, name=partName, type=DEFORMABLE_BODY)
	M.parts[partName].BaseShell(sketch=M.sketches['__profile__'])
	del M.sketches['__profile__']

	#Assign section
	M.parts[partName].SectionAssignment(offset=0.0, 
	    offsetField='', offsetType=MIDDLE_SURFACE, region=Region(
	    faces=M.parts[partName].faces.findAt(((0.0, 
	    0.0, 0.0), ), )), sectionName='Slab', 
	    thicknessAssignment=FROM_SECTION)

	#Assign Rebar Orientation
	M.parts[partName].assignRebarOrientation(
	    additionalRotationType=ROTATION_NONE, axis=AXIS_1,
	    fieldName='', localCsys=None, orientationType=GLOBAL,
	    region=Region(faces=M.parts[partName].faces.findAt(
	    ((0.1, 0.1, 0.0), (0.0, 0.0, 1.0)), )))




def createSets(M, col_height):
	'''
	Create part sets. Will be available in assembly as well.
	Naming in assembly: partName_an-e.setName (an-e are coordinates)
	
	M:		Model
	'''

	# Column base/top
	M.parts['COLUMN'].Set(name='col-base', vertices=
	    M.parts['COLUMN'].vertices.findAt(((0.0, 0.0, 0.0),)))		
	M.parts['COLUMN'].Set(name='col-top', vertices=
	    M.parts['COLUMN'].vertices.findAt(((0.0, col_height, 0.0),)))



def createSurfs(M):
	'''
	Create part surfaces. Will be available in assembly as well.
	Naming in assembly: partName_an-e.surfName (an-e are coordinates)
	
	Parameters
	M:		Model
	'''

	#Slab top and bottom
	M.parts['SLAB'].Surface(name='topSurf', side1Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))
	M.parts['SLAB'].Surface(name='botSurf', side2Faces=
	    M.parts['SLAB'].faces.findAt(((0.0, 0.0, 0.0), )))


	#Circumferential beam surfaces
	circumEdges = M.parts['BEAM'].edges.findAt(((2000.0, 0.0, 0.0), ))
	M.parts['BEAM'].Surface(circumEdges=circumEdges, name='surf')



def createAssembly(M, x, z, y, x_d, z_d, y_d):
	'''
	Creates an assembly of columns, beams and slabs.

	Parameters:
	M:		Model
	x,z,y:	Nr of bays and floors
	x_d:	Size of bays in x direction
	z_d:	Size of bays in z direction
	y_d:	Floor height
	'''

	#Create coordinate list
	#Letters go left to right (positive x)
	#Number top to bottom (positive z)
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	etg = map(str,range(1,y+1))

	#Lists of all instances
	columnList = []
	beamList = []
	slabList = []

	#================ Columns ==================#
	count=-1
	for a in alph:
		count = count + 1
		for n in numb:
			for e in etg:
				inst = 'COLUMN_' + a + n + "-" + e
				columnList.append(inst)
				#import and name instance
				M.rootAssembly.Instance(dependent=ON,
					name= inst,
					part=M.parts['COLUMN'])
				#Translate instance in x,y and z
				M.rootAssembly.translate(instanceList=(inst, ),	
					vector=(x_d*count , y_d*(int(e)-1),
					z_d*(int(n)-1)))

	#================ Beams ==================#
	#Beams in x (alpha) direction
	for a in range(len(alph)-1):
		for n in range(len(numb)-0):
			for e in range(len(etg)):
				inst = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]		
				beamList.append(inst)
				#import and name instance
				M.rootAssembly.Instance(dependent=ON,name=inst,
					part=M.parts['BEAM'])
				M.rootAssembly.translate(instanceList=(inst, ),
					vector=(x_d*a , y_d*(e+1), z_d*n))

	#Beams in z (numb) direction
	#a=0
	for a in [0,x-1]:
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'BEAM_'+ alph[a]+numb[n] + "-" + alph[a]+ \
					numb[n+1] + "-"+etg[e]
				beamList.append(inst)
				# import and name instance
				M.rootAssembly.Instance(dependent=ON,name=inst,
					part=M.parts['BEAM'])
				# Rotate instance
				M.rootAssembly.rotate(angle=-90.0, axisDirection=(
					0.0,1.0, 0.0), axisPoint=(0.0, 0.0, 0.0),
					instanceList=(inst, ))
				# Translate instance in x,y and z
				M.rootAssembly.translate(instanceList=(inst, ),
					vector=(x_d*a , y_d*(e+1), z_d*n))	


	#================ Slabs ==================#
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				slabList.append(inst)
				M.rootAssembly.Instance(dependent=ON,name=inst,
					part=M.parts['SLAB'])
				M.rootAssembly.rotate(angle=-90.0, axisDirection=(
					1.0,0.0, 0.0), axisPoint=(0.0, 0.0, 0.0),
					instanceList=(inst, ))
				M.rootAssembly.translate(instanceList=(inst, ),
					vector=(x_d*a,y_d*(e+1),z_d*(n+1)))



def mesh(M, seed):
	'''
	Meshes all parts with a global seed

	Parameters.
	M:		Model
	seed:	Global seed
	'''

	#Same seed for all parts
	seed1 = seed2 = seed3 = seed

	analysisType = STANDARD  #Could be STANDARD or EXPLICIT
		#This only controls what elements are available to choose from

	element1 = B31 #B31 or B32 for linear or quadratic
	element2 = element1
	element3 = S4R 	#S4R or S8R for linear or quadratic
					#(S8R is not available for Explicit)

	#================ Column ==================#
	#Seed
	M.parts['COLUMN'].seedPart(minSizeFactor=0.1, size=seed1)
	#Change element type
	M.parts['COLUMN'].setElementType(elemTypes=(ElemType(
		elemCode=element1, elemLibrary=analysisType), ), regions=(
		M.parts['COLUMN'].edges.findAt((0.0, 0.0, 0.0), ), ))
	#Mesh
	M.parts['COLUMN'].generateMesh()

	#================ Beam ==================#
	#Seed
	M.parts['BEAM'].seedPart(minSizeFactor=0.1, size=seed2)
	#Change element type
	M.parts['BEAM'].setElementType(elemTypes=(ElemType(
		elemCode=element2, elemLibrary=analysisType), ), regions=(
		M.parts['BEAM'].edges.findAt((0.0, 0.0, 0.0), ), ))
	#Mesh
	M.parts['BEAM'].generateMesh()

	#================ Slab ==================#
	#Seed
	M.parts['SLAB'].seedPart(minSizeFactor=0.1, size=seed3)
	#Change element type
	M.parts['SLAB'].setElementType(elemTypes=(ElemType(
		elemCode=S4R, elemLibrary=analysisType, secondOrderAccuracy=OFF, 
		hourglassControl=DEFAULT), ElemType(elemCode=S3R,
		elemLibrary=analysisType)), 
		regions=(M.parts['SLAB'].faces.findAt((0.0, 0.0, 0.0), ), ))
	#Mesh
	M.parts['SLAB'].generateMesh()





def elmCounter(M):
	'''
	Counts the total number of elements in model M.

	Returns:
	Number of elements
	'''
	nrElm = 0
	for inst in M.rootAssembly.instances.values():
		n = len(inst.elements)
		nrElm = nrElm + n
	return nrElm





def createJoints(M, x, z, y, x_d, z_d, y_d):
	'''
	Joins beams, columns and slabs with constraints.
	Beams are joined to columns with with MPC
	Columns are joined to columns with MPC
	Slabs are tied to beams with tie constrains.
	Slabs are only tied to beams in x direction to create one way slabs.

	Parameters:
	M:		Model
	x,z,y:	Nr of bays and floors
	x_d:	Size of bays in x direction
	z_d:	Size of bays in z direction
	y_d:	Floor height
	'''

	#MPC type for beam to column joints
	beamMPC = TIE_MPC	#May be TIE/BEAM/PIN (Tie will fix)
	colMPC = TIE_MPC



	#Set coordinates to Cartesian
	M.rootAssembly.DatumCsysByDefault(CARTESIAN)

	#Create coordinate list
	#Letters go left to right (positive x)
	#Number top to bottom (positive z)
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	etg = map(str,range(1,y+1))

	#Lists of all instances
	columnList = []
	beamList = []
	slabList = []



	#=========== Beams to columns  ============#
	

	#Column to beam in x(alpha) direction
	for a in range(len(alph)-1):
		for n in range(len(numb)):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),\
					csys=None, mpcType=beamMPC,
					name=constrName, surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)

	#Column to beam in negative x(alpha) direction
	for a in range(len(alph)-1, 0,-1):
		for n in range(len(numb)):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a-1]+numb[n] + "-" + \
					alph[a]+numb[n] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a-1]+numb[n] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					csys=None, mpcType=beamMPC, 
					name=constrName, surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )), userMode=DOF_MODE_MPC, userType=0)

	#Column to beam in z(num) direction
	for a in [0,x-1]:
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a]+numb[n+1] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a]+numb[n+1] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					csys=None, mpcType=beamMPC, name=constrName,
					surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)

	#Column to beam in negative z(num) direction
	for a in [0,x-1]:
		for n in range(len(numb)-1,0,-1):
			for e in range(len(etg)):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				beam = 'BEAM_'+ alph[a]+numb[n-1] + "-" +\
					alph[a]+numb[n] + "-"+etg[e]
				constrName = 'Const_col_beam_'+ alph[a]+numb[n] + "-" + \
					alph[a]+numb[n-1] + "-"+etg[e]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),\
					csys=None, mpcType=beamMPC, name=constrName,
					surface=Region(
					vertices=M.rootAssembly.instances[beam].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)




	#================ Column to column joints =============#

	for a in range(len(alph)):
		for n in range(len(numb)):
			for e in range(len(etg)-1):
				col = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e]
				col2 = 'COLUMN_'+ alph[a]+numb[n] + "-" +etg[e+1]
				constrName = 'Const_col_col_'+ alph[a]+numb[n] + "-"+ \
					etg[e] + "-"+etg[e+1]
				#MPC
				M.MultipointConstraint(controlPoint=Region(
					vertices=M.rootAssembly.instances[col].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					csys=None, mpcType=colMPC, name=constrName,
					surface=Region(
					vertices=M.rootAssembly.instances[col2].vertices.findAt(
					((a*x_d, (e+1)*y_d, n*z_d), ), )),
					userMode=DOF_MODE_MPC, userType=0)
		



	#================ Slabs to beams =============#
	#Uses tie and not MPC


	#Join beam surfaces that are to be constrained
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				beam1 = 'BEAM_'+ alph[a]+numb[n] + "-" + \
					alph[a+1]+numb[n] + "-"+etg[e]
				beam2 = 'BEAM_'+ alph[a]+numb[n+1] + "-" + \
					alph[a+1]+numb[n+1] + "-"+etg[e]
				M.rootAssembly.SurfaceByBoolean(name=inst+'_beamEdges', 
					surfaces=(
					M.rootAssembly.instances[beam1].surfaces['surf'],
					M.rootAssembly.instances[beam2].surfaces['surf']
					))

	#=========== Slab edge surfaces  ============#
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				M.rootAssembly.Surface(name=inst+'_edges', side1Edges=
					M.rootAssembly.instances[inst].edges.findAt(
					((x_d*a+1, y_d*(e+1), z_d*n), ),
					((x_d*a+1, y_d*(e+1), z_d*n+x_d), ),
					))

	#Tie slabs to beams (beams as master)
	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n] + "-"+etg[e]
				M.Tie(adjust=ON, master=
					M.rootAssembly.surfaces[inst+'_beamEdges'],
					name=inst, positionToleranceMethod=COMPUTED, slave=
					M.rootAssembly.surfaces[inst+'_edges']
					, thickness=OFF, tieRotations=OFF)


def fixColBase(M, x, z):
	'''
	Fixes all column bases

	Parameters:
	M: 		Model
	x, z 	Nr of bays
	'''

	#Create coordinate list
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))

	for a in alph:
		for n in numb:
			colSet = 'COLUMN_' + a + n + "-" + "1.col-base"
			M.DisplacementBC(amplitude=UNSET, createStepName=
				'Initial', distributionType=UNIFORM, fieldName='', fixed=OFF,
				localCsys=None, name=colSet, region=
				M.rootAssembly.sets[colSet], u1=0.0, u2=0.0, u3=0.0
				, ur1=0.0, ur2=0.0, ur3=0.0)


#===================================================#
#===================================================#
#               STEP DEPENDENT FUNCTIONS           	#
#===================================================#
#===================================================#

def addSlabLoad(M, x, z, y, step, load):
	'''
	Adds a surface traction to all slabs

	Parameters:
	M: 		 Model
	load: 	 Magnitude of load (positive y)
	x, z, y: Nr of bays
	Step:	 Which step to add the load
	'''

	#Create coordinate list
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	etg = map(str,range(1,y+1))

	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n]+"-"+etg[e]
				M.SurfaceTraction(createStepName=step, 
					directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
					distributionType=UNIFORM, field='', follower=OFF,
					localCsys=None, magnitude= load,
					name="Slab_" + alph[a]+numb[n]+"-"+etg[e],
					region=M.rootAssembly.instances[inst].surfaces['topSurf'],
					traction=GENERAL)





#===========================================================#
#===========================================================#
#                   JOB AND POST                            #
#===========================================================#
#===========================================================#


class clockTimer(object):
	"""
	Class for taking the wallclocktime of an analysis.
	Uses the python function datetime to calculate the elapsed time.
	"""
	def __init__(self):
		self.model = None
    
	def start(self, model):
		'''
		Start a timer

		model = name of model to time
		'''
		self.startTime = datetime.now()
		self.model = model
    
	def end(self, fileName):
		'''
		End a timer and write result to file

		fileName = name of file to write result to
		'''
		t = datetime.now() - self.startTime
		time = str(t)[:-7]
		with open(fileName,'a') as f:
			text = '%s	wallClockTime:	%s\n' % (self.model, time) 
			f.write(text)



def runJob(jobName):
	print 'Running %s...' %jobName

	'''
	Need to run jobs with an exeption in order to continue after riks step.
	The step is not completed but aborted when it reached max LPF.
	Also if maximum nr of increments is reach I still whant to be able to 
	do post proccesing'''

	#Create and start timer
	timer = clockTimer()
	timer.start(jobName)

	#Run job
	try:
		mdb.jobs[jobName].submit(consistencyChecking=OFF)	#Run job
		mdb.jobs[jobName].waitForCompletion()
	except:
		print 'runJob Exeption:'
		print mdb.jobs[jobName].status

	#End timer and write result to file
	timer.end('results.txt')

	#=========== Display Job  ============#
	#Open odb
	odb = open_odb(jobName)
	#View odb in viewport
	V=session.viewports['Viewport: 1']
	V.setValues(displayedObject=odb)
	V.odbDisplay.display.setValues(plotState=(
		CONTOURS_ON_DEF, ))
	V.odbDisplay.commonOptions.setValues(
		deformationScaling=UNIFORM, uniformScaleFactor=10)




def staticCPUtime(jobName, fileName):
	'''
	Reads CPU time from .msg file and writes that to file

	jobName  = model to read CPU time for
	fileName = name of file to write result
	'''
	#Print CPU time to file
	with open(jobName+'.msg') as f:
		lines = f.readlines()

	cpuTime = lines[-2]
	with open(fileName, 'a') as f:
		f.write(jobName + '	' +cpuTime+'\n')


#=========== Post proccesing  ============#


def open_odb(odbPath):
	"""
	Enter odbPath (with or without extension)
	and get upgraded (if necesarly)
	
	Parameters
	odb = openOdb(odbPath)

	Returns
	open odb object
	"""
	#Allow both .odb and without extention
	base, ext = os.path.splitext(odbPath)
	odbPath = base + '.odb'
	new_odbPath = None
	#Check if odb needs upgrade
	if isUpgradeRequiredForOdb(upgradeRequiredOdbPath=odbPath):
		print('odb %s needs upgrading' % (odbPath,))
		path,file_name = os.path.split(odbPath)
		file_name = base + "_upgraded.odb"
		new_odbPath = os.path.join(path,file_name)
		upgradeOdb(existingOdbPath=odbPath, upgradedOdbPath=new_odbPath)
		odbPath = new_odbPath
	odb = openOdb(path=odbPath, readOnly=True)
	return odb





def XYprint(odbName, plotName, printFormat, *args):
	'''
	Prints XY curve(s) to file

	odbName     = name of odbFile
	plotName    = name to give plot
	printFormat = TIFF, PS, EPS, PNG, SVG
	*args       = curve(s) to plot
	'''

	V=session.viewports['Viewport: 1']
	#Open ODB
	odb = open_odb(odbName)
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
	session.printToFile(fileName='XY_'+plotName,format=printFormat,
		canvasObjects=(V, ))




def countourPrint(odbName, defScale, printFormat):
	'''
	Plots countour plots to file.

	odbName  =	name of odb
	defScale =  Deformation scale
	printFormat = TIFF, PS, EPS, PNG, SVG
	'''

	#Open odb
	odb = open_odb(odbName)
	#Create object for viewport
	V=session.viewports['Viewport: 1']
	#View odb in viewport
	V.setValues(displayedObject=odb)
	V.odbDisplay.display.setValues(plotState=(
		CONTOURS_ON_DEF, ))
	V.odbDisplay.commonOptions.setValues(
		deformationScaling=UNIFORM, uniformScaleFactor=defScale)

	#Print plots at the last frame in each step
	session.printOptions.setValues(vpBackground=ON, compass=ON)
	for step in odb.steps.keys():
		V.odbDisplay.setFrame(step=step, frame=-1)
		#VonMises
		V.odbDisplay.setPrimaryVariable(
			variableLabel='S', outputPosition=INTEGRATION_POINT,
			refinement=(INVARIANT, 'Mises'), )
		session.printToFile(fileName='Cont_VonMises_'+step,
			format=printFormat, canvasObjects=(V, ))
		#PEEQ
		V.odbDisplay.setPrimaryVariable(
			variableLabel='PEEQ', outputPosition=INTEGRATION_POINT, )
		session.printToFile(fileName='Cont_PEEQ_'+step,
			format=printFormat, canvasObjects=(V, ))




def xyEnergyPrint(odbName, printFormat):
	'''
	Prints External work, internal energy and kinetic energy for 
	whole model

	odbName     = name of odb
	printFormat = TIFF, PS, EPS, PNG, SVG
	'''

	plotName = 'Energy'

	#Open ODB
	odb = open_odb(odbName)
	#Create curves to plot
	xy1 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='External work: ALLWK for Whole Model', 
		suppressQuery=True)
	c1 = session.Curve(xyData=xy1)
	xy2 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='Internal energy: ALLIE for Whole Model', 
		suppressQuery=True)
	c2 = session.Curve(xyData=xy2)
	xy3 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName='Kinetic energy: ALLKE for Whole Model', 
		suppressQuery=True)
	c3 = session.Curve(xyData=xy3)
	#Plot and Print
	XYprint(odbName, plotName, printFormat, c1, c2, c3)




def xyAPMcolPrint(odbName, column, printFormat):
	'''
	Prints U2 at top of removed column in APM.

	odbName = name of odb
	column  = name of column that is removed in APM
	printFormat = TIFF, PS, EPS, PNG, SVG
	'''

	plotName = 'U2_APMCol'

	#Open ODB
	odb = open_odb(odbName)
	#Find correct historyOutput
	for key in odb.steps[stepName].historyRegions.keys():
		if key.find('Node '+column) > -1:
			histName = key
	histOpt = odb.steps[stepName].historyRegions[histName].historyOutputs
	#Get node number
	nodeNr = histName[-1]
	#Create XY-curve
	xy1 = xyPlot.XYDataFromHistory(odb=odb, 
		outputVariableName=
		'Spatial displacement: U2 PI: '+column+' Node '+nodeNr+' in NSET COL-TOP', 
		suppressQuery=True)
	c1 = session.Curve(xyData=xy1)
	#Plot and Print
	XYprint(jobName, plotName, printFormat, c1)






#==================================================#
#==================================================#
#                   APM                            #
#==================================================#
#==================================================#


def historySectionForces(M, column, stepName):
	#Section forces and moments of top element in column to be deleted
	elmNr = M.rootAssembly.instances[column].elements[-1].label
	elm = M.rootAssembly.instances[column].elements[elmNr-1:elmNr]
	M.rootAssembly.Set(elements=elm, name='topColElm')

	M.HistoryOutputRequest(name='SectionForces', createStepName=stepName,
		variables=('SF1', 'SF2', 'SF3', 'SM1', 'SM2', 
		'SM3'), region=M.rootAssembly.sets['topColElm'],)



def addSmoothSlabLoad(M, x, z, y, step, load, amplitude):
	'''
	Adds a surface traction to all slabs with an amplitude

	Parameters:
	M: 		 Model
	load: 	 Magnitude of load (positive y)
	x, z, y: Nr of bays
	Step:	 Which step to add the load
	amplitude: Name of amplitude
	'''

	#Create coordinate list
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	etg = map(str,range(1,y+1))

	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n]+"-"+etg[e]
				M.SurfaceTraction(createStepName=step, 
					directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
					distributionType=UNIFORM, field='', follower=OFF,
					localCsys=None, magnitude= load,
					name="Slab_" + alph[a]+numb[n]+"-"+etg[e],
					region=M.rootAssembly.instances[inst].surfaces['topSurf'],
					traction=GENERAL,  amplitude=amplitude)


def replaceForces(M, column, oldJob, oldStep, stepName, amplitude):
	'''
	Remove col-base BC or col-col constraint
	and add forces and moments from static analysis to top of colum

	M         = Model
	column    = column to be deleted in APM
	oldJob    = name of static job
	oldSte    = name of static step
	amplitude = name of amplitude to add forces with
	'''

	#Delete col-base BC or col-col constraint
	if column[-1] == '1':
		del M.boundaryConditions[column+'.col-base']
	else:
		topColNr = column[-1]
		botColNr = str(int(topColNr)-1)
		constName = 'Const_col_col_'+ column[-4:-1]+botColNr+'-'+topColNr
		del M.constraints[constName]

	#Open odb with static analysis
	odb = open_odb(oldJob)

	#Find correct historyOutput
	for key in odb.steps[oldStep].historyRegions.keys():
		if key.find('Element '+column) > -1:
			histName = key

	#Create dictionary with forces
	dict = {}
	histOpt = odb.steps[oldStep].historyRegions[histName].historyOutputs
	variables = histOpt.keys()
	for var in variables:
		value = histOpt[var].data[-1][1]
		dict[var] = value

	#Where to add forces
	region = M.rootAssembly.instances[column].sets['col-top']

	#Create forces
	M.ConcentratedForce(name='Forces', 
		createStepName=stepName, region=region, amplitude=amplitude,
		distributionType=UNIFORM, field='', localCsys=None,
		cf1=dict['SF3'], cf2=-dict['SF1'], cf3=dict['SF2'])

	#Create moments
	M.Moment(name='Moments', createStepName=stepName, 
		region=region, distributionType=UNIFORM, field='', localCsys=None,
		amplitude=amplitude, 
		cm1=dict['SM2'], cm2=-dict['SM3'], cm3=dict['SM1'])





#====================================================#
#====================================================#
#                   Blast                            #
#====================================================#
#====================================================#



def createBlastAmp(M):
	'''
	Reads data from 'blast.csv' and created an amplitude

	M = model
	'''
	
	table=[]
	with open('ProgressiveCollapse/blast.csv', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		for row in reader:
			table.append((float(row[0]), float(row[1])))
			blastTime = float(row[0])

	tpl = tuple(table)
	M.TabularAmplitude(name='Blast', timeSpan=STEP, 
	   	smooth=SOLVER_DEFAULT, data=(tpl))




def createRPs(M, source, standoff):
	'''
	Creates two reference points, 'Source' and 'Standoff'

	M        = Model
	source   = Coordinates(tuple)
	standoff = Coordinates(tuple)
	'''

	ass = M.rootAssembly

	#Source Point
	feature = ass.ReferencePoint(point=source)
	ID = feature.id
	sourceRP = ass.referencePoints[ID]
	ass.Set(name='Source', referencePoints=(sourceRP,))

	#Standoff Point
	feature = ass.ReferencePoint(point=standoff)
	ID = feature.id
	standoffRP = ass.referencePoints[ID]
	ass.Set(name='Standoff', referencePoints=(standoffRP,))


def blastSurf(M):
	'''
	Creates column surfaces (since they do not allready exict) and join
	all column, beam and bottom slab surfaces to one surface: 'blastSurf'

	M = Model
	'''

	ass = M.rootAssembly


	#Create circumferential column surfaces
	circumEdges = M.parts['COLUMN'].edges.findAt(((0.0, 10.0, 0.0), ))
	M.parts['COLUMN'].Surface(circumEdges=circumEdges, name='surf')

	#Join blast surfaces
	lst = []
	for inst in ass.instances.keys():
		if inst.startswith('BEAM') or inst.startswith('COLUMN'):
			lst.append(ass.instances[inst].surfaces['surf'])
		if inst.startswith('SLAB'):
			lst.append(ass.instances[inst].surfaces['botSurf'])
	blastSurf = tuple(lst)
	ass.SurfaceByBoolean(name='blastSurf', surfaces=blastSurf)





def animate(odbName, defScale, frameRate):
	'''
	Animates the deformation with Von Mises contour plot
	Each field output frame is a frame in the animation
	(that means the animation time is not real time)

	odbName = name of job
	defScal = deformation scale
	frameRate = frame rate
	'''
	
	#Open odb
	odb = open_odb(odbName)
	#Create object for viewport
	V=session.viewports['Viewport: 1']

	#View odb in viewport
	V.setValues(displayedObject=odb)
	V.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
	V.odbDisplay.commonOptions.setValues(
		deformationScaling=UNIFORM, uniformScaleFactor=defScale)
	V.odbDisplay.setPrimaryVariable(
		variableLabel='S', outputPosition=INTEGRATION_POINT,
		refinement=(INVARIANT, 'Mises'), )

	#Create and save animation
	session.animationController.setValues(animationType=TIME_HISTORY,
		viewports=(V.name,))
	session.animationController.play()
	session.imageAnimationOptions.setValues(frameRate = frameRate,
		compass = ON, vpBackground=ON)
	session.writeImageAnimation(fileName=odbName, format=QUICKTIME,
		canvasObjects=(V, )) #format = QUICKTIME or AVI

	#Stop animation
	session.animationController.stop()

