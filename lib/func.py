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






#===============================================================#
#===============================================================#
#                   PERLIMINARY		                            #
#===============================================================#
#===============================================================#




def perliminary(monitor, modelName):
	#Makes mouse clicks into physical coordinates
	session.journalOptions.setValues(replayGeometry=COORDINATE,
		recoverGeometry=COORDINATE)

	#Print begin script to console
	print '\n'*6
	print '###########    NEW SCRIPT    ###########'
	print str(datetime.now())[:19]

	#Print status to console during analysis
	if monitor:
		printStatus(ON)

	#Create text file to write results in
	with open('results.txt', 'w') as f:
		None


	#=========== Set up model  ============#
	matFile = 'inputData/steelMat.inp'

	#Create model based on input material
	print '\n'*2
	mdb.ModelFromInputFile(name=modelName, inputFileName=matFile)
	print '\n'*2

	#Deletes all other models
	delModels(modelName)

	#Close and delete old jobs and ODBs
	delJobs(exeption = matFile)


	#=========== Material  ============#
	#Material names
	steel = 'DOMEX_S355'
	concrete = 'Concrete'


	M=mdb.models[modelName]
	createMaterials(M, mat1=steel, mat2=concrete)



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




#=========== Model ions  ============#

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






#=========== Materials  ============#


def createMaterials(M, mat1, mat2):
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
	mat2_yield = 30.0		#Yield stress in compression
	mat2_yieldTension = 2.0 #Yield stress in compression

	


	#=========== Steel  ============#
	#Steel is already imported but needs damping
	M.materials[mat1].Damping(alpha=damping)

	#================ Concrete ==================#
	M.Material(description=mat2_Description, name=mat2)
	M.materials[mat2].Density(table=((mat2_dens, ), ))
	M.materials[mat2].Elastic(table=((mat2_E, mat2_v), ))
	# M.materials[mat2].Plastic(table=((mat2_yield, 0.0), ))
	M.materials[mat2].Damping(alpha=damping)
	M.materials[mat2].ConcreteDamagedPlasticity(
	    table=((30.0, 0.1, 1.16, 0.0, 0.0), ))
	    #Dilatation angle, Eccentricity, fb0/fc0, K, Viscosity parameter
	M.materials[mat2].concreteDamagedPlasticity.ConcreteCompressionHardening(
	    table=((mat2_yield, 0.0), ))
	M.materials[mat2].concreteDamagedPlasticity.ConcreteTensionStiffening(
	    table=((mat2_yieldTension, 0.0), ))





















#======================================================#
#======================================================#
#                   LOADING                            #
#======================================================#
#======================================================#

#=========== Slab load ions for beam model  ============#


def addSlabLoad(M, x, z, y, step, load, amplitude=UNSET):
	'''
	Adds a surface traction to all slabs

	Parameters:
	M: 		 Model
	load: 	 Magnitude of load (positive y)
	x, z, y: Nr of bays
	Step:	 Which step to add the load
	Amplitude: default is UNSET
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
					name=inst,
					region=M.rootAssembly.instances[inst].surfaces['topSurf'],
					traction=GENERAL, amplitude = amplitude)


def changeSlabLoad(M, x, z, y, step, amplitude):
	'''
	Change 

	Parameters:
	M: 		 Model
	load: 	 Magnitude of load (positive y)
	x, z, y: Nr of bays
	Step:	 Which step to add the load
	Amplitude: default is UNSET
	'''

	#Create coordinate list
	alph = map(chr, range(65, 65+x)) #Start at 97 for lower case letters
	numb = map(str,range(1,z+1))
	etg = map(str,range(1,y+1))

	for a in range(len(alph)-1):
		for n in range(len(numb)-1):
			for e in range(len(etg)):
				inst = 'SLAB_'+ alph[a]+numb[n]+"-"+etg[e]
				M.loads[inst].setValuesInStep(stepName = step,
					amplitude = amplitude)








#=========== Blast ions  ============#


def addIncidentWave(modelName, stepName, AmpFile, sourceCo, refCo):
	airDensity = 1.225e-12    #1.225 kg/m^3
	soundSpeed =340.29e3    # 340.29 m/s

	M=mdb.models[modelName]

	#Pressure amplitude from file blastAmp.csv
	firstRow=1
	table=[]
	with open('inputData/'+AmpFile, 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		for row in reader:
			if firstRow: 
				firstRow=0
			else:
				table.append((float(row[0]), float(row[1])))
				blastTime = float(row[0])
	tpl = tuple(table)
	M.TabularAmplitude(name='Blast', timeSpan=STEP, 
	   	smooth=SOLVER_DEFAULT, data=(tpl))


	#Source Point
	feature = M.rootAssembly.ReferencePoint(point=sourceCo)
	ID = feature.id
	sourceRP = M.rootAssembly.referencePoints[ID]
	M.rootAssembly.Set(name='Source', referencePoints=(sourceRP,))

	#Standoff Point
	feature = M.rootAssembly.ReferencePoint(point=refCo)
	ID = feature.id
	standoffRP = M.rootAssembly.referencePoints[ID]
	M.rootAssembly.Set(name='Standoff', referencePoints=(standoffRP,))


	#Create interaction property
	M.IncidentWaveProperty(name='Blast', 
	    definition=SPHERICAL, fluidDensity=airDensity, soundSpeed=soundSpeed)


	#Create incident Wave Interaction
	M.IncidentWave(name='Blast', createStepName=stepName, 
	    sourcePoint=M.rootAssembly.sets['Source'],
	    standoffPoint=M.rootAssembly.sets['Standoff'],
	    surface=M.rootAssembly.surfaces['blastSurf'],
	    definition=PRESSURE, interactionProperty='Blast', 
	    referenceMagnitude=1.0, amplitude='Blast')


	#Set model wave formulation (does not matter when fluid is not modeled)
	M.setValues(waveFormulation=TOTAL)



def addConWep(modelName, TNT, blastType, coordinates,timeOfBlast, stepName):
	'''
	blastType = AIR_BLAST SURFACE_BLAST
	name of surf must be blastSurf

	time: Time of blast, NB: total time
	OfBlast	'''
	M=mdb.models[modelName]

	#Create interaction property
	M.IncidentWaveProperty(definition= blastType,
	    massTNT=TNT,
	    massFactor=1.0e3,
	    lengthFactor=1.0e-3,
	    pressureFactor=1.0e6,
	    name='IntProp-1',)

	#Source Point
	feature = M.rootAssembly.ReferencePoint(point=coordinates)
	ID = feature.id
	sourceRP = M.rootAssembly.referencePoints[ID]
	M.rootAssembly.Set(name='Source', referencePoints=(sourceRP,))
	
	

	#Create ineraction
	M.IncidentWave(createStepName=stepName, definition=CONWEP, 
	    detonationTime=timeOfBlast, interactionProperty='IntProp-1',
	 	name='Int-1',
	    sourcePoint=M.rootAssembly.sets['Source'], 
	    surface=M.rootAssembly.surfaces['blastSurf'])


















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




def xyAPMcolPrint(odbName, column, printFormat, stepName):
	'''
	Prints U2 at top of removed column in APM.
	odbName     = name of odb
	column      = name of column that is removed in APM
	printFormat = TIFF, PS, EPS, PNG, SVG
	stepName    = name of first step (will print data from this and out)		
				  plot it not affected by this as long as the
				  stepName exists
	'''

	plotName = 'APMcolU2'

	#Open ODB
	odb = open_odb(odbName)
	#Find correct historyOutput
	for key in odb.steps[stepName].historyRegions.keys():
		if key.find('Node '+column) > -1:
			histName = key
	#Get node number
	nodeNr = histName[-1]
	varName ='Spatial displacement: U2 PI: '+column+' Node '+nodeNr+' in NSET COL-TOP'
	#Create XY-curve
	xy1 = xyPlot.XYDataFromHistory(odb=odb, outputVariableName=varName, 
		suppressQuery=True)
	c1 = session.Curve(xyData=xy1)
	#Plot and Print
	XYprint(odbName, plotName, printFormat, c1)

	#=========== Data  ============#
	#Report data
	tempFile = '_____temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy1, ))
	fixReportFile(tempFile, plotName, odbName)





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






def getElmOverLim(odbName, var, stepName, var_invariant, limit,
		elsetName=None):
	"""
	Returns list with value and object for all elements over limit
	odbName       = name of odb to read from
	elsetName     = None, (may be set to limit what part of the model 
					to read)
	var           = 'PEEQ' or 'S'
	stepName      = Last step in odb
	var_invariant = 'mises' if var='S'
	limit         = var limit for what elements to return
	"""
	elset = elemset = None
	region = "over the entire model"
	odb = open_odb(odbName)
	
	#Check to see if the element set exists in the assembly
	if elsetName:
		try:
			elemset = odb.rootAssembly.elementSets[elsetName]
			region = " in the element set : " + elsetName;
		except KeyError:
			print 'An assembly level elset named %s does' \
				'not exist in the output database %s' \
				% (elsetName, odbName)
			odb.close()
			exit(0)
	
	#Find values over limit
	step = odb.steps[stepName]
	result = []
	for frame in step.frames:
		allFields = frame.fieldOutputs
		if (allFields.has_key(var)):
			varSet = allFields[var]
			if elemset:
				varSet = varSet.getSubset(region=elemset)      
			for varValue in varSet.values:
				if var_invariant:
					if hasattr(varValue, var_invariant.lower()):
						val = getattr(varValue,var_invariant.lower())
					else:
						raise ValueError('Field value does not have invariant %s' % (var_invariant,))
				else:
					val = varValue.data
				if ( val >= limit):
					result.append([val,varValue])
		else:
			raise ValueError('Field output does not have field %s' % (results_field,))
	return (result)



def delInstance(M, elmOverLim, stepName):
	'''
	Takes a list of elements and deletes the corresponding columns and beams.
	M          = model
	elmOverLim = list of elements
	stepname   = In what step to delete instances
	'''

	instOverLim = []
	#Create list of all instance names
	for i in range(len(elmOverLim)):
		instOverLim.append(elmOverLim[i][1].instance.name)

	#Create list with unique names
	inst = []
	for i in instOverLim:
		if i not in inst:
			inst.append(i)

	#Remove slabs so they are not deleted
	instFiltered=[]
	for i in inst[:]:
		if not i.startswith('SLAB'):
			instFiltered.append(i)

	#Merge set of instances to be deleted
	setList=[]
	for i in instFiltered:
		setList.append(M.rootAssembly.allInstances[i].sets['set'])

	setList = tuple(setList)
	if setList:
		M.rootAssembly.SetByBoolean(name='rmvSet', sets=setList)
	else:
		print 'No instances exceed criteria'
		
	#Remove instances
	M.ModelChange(activeInStep=False, createStepName=stepName, 
		includeStrain=False, name='INST_REMOVAL', region=
		M.rootAssembly.sets['rmvSet'], regionType=GEOMETRY)

















#===========================================================#
#===========================================================#
#                   JOB AND POST                            #
#===========================================================#
#===========================================================#


class clockTimer(object):
	"""
	Class for taking the wallclocktime of an analysis.
	Uses the python ion datetime to calculate the elapsed time.
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
		deformationScaling=UNIFORM, uniformScaleFactor=1)




def readMsgFile(jobName, fileName):
	'''
	Reads CPU time and nr of increments from .msg file
	and writes that to fileName

	jobName  = model to read CPU time for
	fileName = name of file to write result
	'''
	#Read .msg file
	with open(jobName+'.msg') as f:
		lines = f.readlines()

	#CPU time
	cpuTime = lines[-2]
	with open(fileName, 'a') as f:
		f.write(jobName + '	' +cpuTime+'\n')

	#Nr of increments
	inc = lines[-22]
	with open(fileName, 'a') as f:
		f.write(jobName + '	' +inc+'\n')	



def readStaFile(jobName, fileName):
	'''
	Reads cpuTime and last stable time increment from .sta file.
	Prints result to fileName
	'''
	#Print CPU time to file
	with open(jobName+'.sta') as f:
		lines = f.readlines()

	cpuTime = lines[-7][32:40]
	stblInc = lines[-7][41:50]
	with open(fileName, 'a') as f:
		f.write(jobName + '	CPUtime ' +cpuTime+'\n')
		f.write(jobName + '	Stable Time Increment ' +stblInc+'\n')


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





def XYprint(modelName, plotName, printFormat, *args):
	'''
	Prints XY plot to file

	modelName     = name of odbFile
	plotName    = name to give plot
	printFormat = TIFF, PS, EPS, PNG, SVG
	*args       = curve(s) to plot
	'''

	
	V=session.viewports['Viewport: 1']
	#Open ODB
	odb = open_odb(modelName)

	#=========== XP plot  ============#
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
	session.printToFile(fileName='XY_'+plotName+'_'+modelName,
		format=printFormat, canvasObjects=(V, ))
	

def fixReportFile(reportFile, plotName, modelName, x, y):
	'''
	Creates a tab file froma stupid report file

	reportFile = name of report file to fix
	plotName   = what is plottes
	modelName    = name of job
	'''

	a=None
	b=None

	fileName = 'xyData_'+plotName+'_'+modelName+'.txt'
	with open(reportFile, 'r') as f:
	    lines = f.readlines()

	with open(fileName, 'w') as f:
		f.write('%s\t%s\n' %(x,y))
		for line in lines:
			lst = line.lstrip().rstrip().split()
			if lst:
				try:
					a = float(lst[0])
					b = float(lst[1])
				except:
					pass
				if type(a) and type(b) is float:
					f.write(lst[0])
					f.write('\t')
					f.write(lst[1])
					f.write('\n')





def countourPrint(modelName, defScale, printFormat):
	'''
	Plots countour plots to file.

	modelName  =	name of odb
	defScale =  Deformation scale
	printFormat = TIFF, PS, EPS, PNG, SVG
	'''

	#Open odb
	odb = open_odb(modelName)
	#Create object for viewport
	V=session.viewports['Viewport: 1']
	#View odb in viewport
	V.setValues(displayedObject=odb)
	V.odbDisplay.display.setValues(plotState=(
		CONTOURS_ON_DEF, ))
	V.odbDisplay.commonOptions.setValues(
		deformationScaling=UNIFORM, uniformScaleFactor=defScale)

	#Print plots at the last frame in each step
	session.printOptions.setValues(vpBackground=OFF, compass=ON)
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




def xyEnergyPrint(modelName, printFormat):
	'''
	Prints External work, internal energy and kinetic energy for 
	whole model

	modelName     = name of odb
	printFormat = TIFF, PS, EPS, PNG, SVG
	'''

	plotName = 'Energy'

	#Open ODB
	odb = open_odb(modelName)
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
	XYprint(modelName, plotName, printFormat, c1, c2, c3)

	#Save xyData
	tempFile = 'temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF,
		xyData=(xy1, ))
	plotName='externalWork'
	fixReportFile(tempFile, plotName, modelName,
		x='Time [s]', y='External work [mJ]')

	session.writeXYReport(fileName=tempFile, appendMode=OFF,
		xyData=(xy2, ))
	plotName='internalEnergy'
	fixReportFile(tempFile, plotName, modelName,
		x='Time [s]', y='Internal Energy [mJ]')

	session.writeXYReport(fileName=tempFile, appendMode=OFF,
		xyData=(xy3, ))
	plotName='kineticEnergy'
	fixReportFile(tempFile, plotName, modelName,
		x='Time [s]', y='Kinetic Energy [mJ]')



def xyAPMcolPrint(modelName, column, printFormat, stepName):
	'''
	Prints U2 at top of removed column in APM.

	modelName     = name of odb
	column      = name of column that is removed in APM
	printFormat = TIFF, PS, EPS, PNG, SVG
	stepName    = name of a step that exist in the model
	'''

	plotName = 'U2'

	#Open ODB
	odb = open_odb(modelName)
	#Find correct historyOutput
	for key in odb.steps[stepName].historyRegions.keys():
		if key.find('Node '+column) > -1:
			histName = key
	#Get node number
	nodeNr = histName[-1]
	varName ='Spatial displacement: U2 PI: '+column+' Node '+nodeNr+' in NSET COL-TOP'
	#Create XY-curve
	xy1 = xyPlot.XYDataFromHistory(odb=odb, outputVariableName=varName, 
		suppressQuery=True)
	c1 = session.Curve(xyData=xy1)
	#Plot and Print
	XYprint(modelName, plotName, printFormat, c1)

	#=========== Data  ============#
	#Report data
	tempFile = '_____temp.txt'
	session.writeXYReport(fileName=tempFile, appendMode=OFF, xyData=(xy1, ))
	fixReportFile(tempFile, plotName, modelName)




def animate(modelName, defScale, frameRate):
	'''
	Animates the deformation with Von Mises contour plot
	Each field output frame is a frame in the animation
	(that means the animation time is not real time)

	modelName = name of job
	defScal = deformation scale
	frameRate = frame rate
	'''
	
	#Open odb
	odb = open_odb(modelName)
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
	session.writeImageAnimation(fileName=modelName, format=QUICKTIME,
		canvasObjects=(V, )) #format = QUICKTIME or AVI

	#Stop animation
	session.animationController.stop()