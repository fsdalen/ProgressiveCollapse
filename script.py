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
col1_height = 200


#Beam
part2 = "Beam"
sect2 = "HUP2"
beam1_len = 200


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
M.ConstrainedSketch(name='__profile__', sheetSize=20.0)
M.sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(beam1_len, 0.0))
M.Part(dimensionality=THREE_D, name=part2, type=DEFORMABLE_BODY)
M.parts[part2].BaseWire(sketch=M.sketches['__profile__'])
del M.sketches['__profile__']

#Assign section
faces = M.parts[part2].faces
M.parts[part2].SectionAssignment(region=(faces, ), sectionName=sect2)



#====================================================================#
#						ASSEMBLY 									 #
#====================================================================#


