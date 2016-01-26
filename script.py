#====================================================================#
#						PRELIMINARIES								 #
#====================================================================#


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


from abaqus import *			#These statements make the basic Abaqus objects accessible to the script... 
from abaqusConstants import *	#... as well as all the Symbolic Constants defined in the Abaqus Scripting Interface.
import odbAccess        		# To make ODB-commands available to the script


#This makes mouse clicks into physical coordinates
session.journalOptions.setValues(replayGeometry=COORDINATE,recoverGeometry=COORDINATE)



#================ Input ==================#
modelName = "basicFrame"
mdb.Model(modelType=STANDARD_EXPLICIT, name=modelName) 	#Create a new model 
M = mdb.models[modelName]								#For simplicity
if len(mdb.models.keys()) > 0:							#Deletes all other models
	a = mdb.models.items()
	for i in range(len(a)):
		b = a[i]
		if b[0] != modelName:
			del mdb.models[b[0]]




#====================================================================#
#						MATERIALS 									 #
#====================================================================#

#================ Input ==================#

# Material 1
mat1 = "Steel"	#Material name
mat1Description = 'This is the description'
mat1_dens = 8.05e-06	#Density
mat1_E = 210000.0		#E-module
mat1_v = 0.3			#Poisson
mat1_yield = 355		#Yield stress



#================ Steel ==================#
M.Material(description=mat1Description, name=mat1)
M.materials[mat1].Density(table=((mat1_dens, ), ))
M.materials[mat1].Elastic(table=((mat1_E, mat1_v), ))
M.materials[mat1].Plastic(table=((mat1_yield, 0.0), ))



#====================================================================#
#						PARTS	 									 #
#====================================================================#

#================ Input ==================#
#Column
part1 = "Column"
sect1 = "HUP"
col1_height = 3000


#Beam
part2 = "Beam"
sect2 = "HUP2"
beam_len = 5000


#================ Column ==================#

#Create Section and profile
M.BoxProfile(a=20.0, b=10.0, name='Profile-1', t1=2.0, uniformThickness=ON)
M.BeamSection(consistentMassMatrix=False, integration=
    DURING_ANALYSIS, material='Steel', name=sect1, poissonRatio=0.3, 
    profile='Profile-1', temperatureVar=LINEAR)

#Create part
M.ConstrainedSketch(name='__profile__', sheetSize=20.0)
M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(0.0, col1_height))
M.Part(dimensionality=THREE_D, name=part1, type=DEFORMABLE_BODY)
M.parts[part1].BaseWire(sketch=M.sketches['__profile__'])
del M.sketches['__profile__']

#Assign section
faces = M.parts[part1].faces
M.parts[part1].SectionAssignment(region=(faces, ), sectionName=sect1)


#================ Beam ==================#

#Create Section and profile
M.BoxProfile(a=20.0, b=10.0, name='Profile-2', t1=2.0, uniformThickness=ON)
M.BeamSection(consistentMassMatrix=False, integration=
    DURING_ANALYSIS, material='Steel', name=sect2, poissonRatio=0.3, 
    profile='Profile-2', temperatureVar=LINEAR)

#Create part
M.ConstrainedSketch(name='__profile__', sheetSize=10000.0)
M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(beam_len, 0.0))
M.Part(dimensionality=THREE_D, name=part2, type=DEFORMABLE_BODY)
M.parts[part2].BaseWire(sketch=M.sketches['__profile__'])
del M.sketches['__profile__']

#Assign section
faces = M.parts[part2].faces
M.parts[part2].SectionAssignment(region=(faces, ), sectionName=sect2)



#====================================================================#
#						ASSEMBLY 									 #
#====================================================================#

#================ Input ==================#
x = 5			#Nr of columns in x direction
z = 4			#Nr of columns in z direction
x_d = beam_len		#Size of bays in x direction
z_d = beam_len		#Size of bays in z direction

y = 3			#nr of stories



#================ Columns ==================#
M.rootAssembly.DatumCsysByDefault(CARTESIAN)  #Set coordinates to Cartesian


#Letters go left to right (positive x)
#Number top to bottom (positive z)

alph = map(chr, range(97, 97+x))
numb = map(str,range(1,z+1))
etg = map(str,range(1,y+1))

count=-1
for a in alph:
	count = count + 1
	for n in numb:
		for e in etg:
			inst = part1 + "_" + a + n + "-" + e
			M.rootAssembly.Instance(dependent=ON,		#import and name instance
				name= inst,
				part=M.parts[part1])
			M.rootAssembly.translate(instanceList=(inst, ),	#Translate instance in x,y and z
				vector=(x_d*count , col1_height*(int(e)-1), z_d*(int(n)-1)))
		

#================ Beams ==================#'

#Beams in x (alpha) direction
for a in range(len(alph)-1):
	for n in range(len(numb)-0):
		for e in range(len(etg)):
			inst = part2+"_"+ alph[a]+numb[n] + "-" + alph[a+1]+numb[n] + "-"+etg[e]		
			#import and name instance
			M.rootAssembly.Instance(dependent=ON,name=inst, part=M.parts[part2])
			M.rootAssembly.translate(instanceList=(inst, ),
				vector=(x_d*a , col1_height*(e+1), z_d*n))

#Beams in z (numb) direction
for a in range(len(alph)-0):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = part2+"_"+ alph[a]+numb[n] + "-" + alph[a]+numb[n+1] + "-"+etg[e]
			#import and name instance
			M.rootAssembly.Instance(dependent=ON,name=inst, part=M.parts[part2])
			#Rotate instance
			M.rootAssembly.rotate(angle=-90.0, axisDirection=(
				0.0,1.0, 0.0), axisPoint=(0.0, 0.0, 0.0), instanceList=(inst, ))
			#Translate instance in x,y and z
			M.rootAssembly.translate(instanceList=(inst, ),
				vector=(x_d*a , col1_height*(e+1), z_d*n))

