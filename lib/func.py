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



#===============================================================#
#===============================================================#
#                   PERLIMINARY		                            #
#===============================================================#
#===============================================================#




def perliminary(monitor, modelName, steel, concrete, rebarSteel):
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
	matFile = 'steelMat.inp'

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
	rebarSteel = 'Rebar Steel'

	M=mdb.models[modelName]
	createMaterials(M, mat1=steel, mat2=concrete, mat3=rebarSteel,)

























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
#                   CREATE MATERIALS                       #
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
	
























 #==============================================================#
 #==============================================================#
 #                   STATIC ANALYSIS                            #
 #==============================================================#
 #==============================================================#

def staticAnalysis(mdbName, modelName, run, static_Type, static_InInc,
	static_MinIncr, static_maxInc, LL_kN_m, defScale, printFormat):

	M=mdb.models[modelName]


	#=========== Step  ============#
	oldStep = 'Initial'
	stepName = 'static'

	if static_Type == 'general':
		M.StaticStep(name=stepName, previous=oldStep, 
			nlgeom=ON, initialInc=static_InInc, minInc=static_MinIncr,
			maxNumInc=static_maxInc)
	elif static_Type == 'riks':
		M.StaticRiksStep(name=stepName, previous=oldStep, 
			nlgeom=ON, initialArcInc=static_InInc, minArcInc=static_MinIncr,
			maxNumInc=static_maxInc, maxLPF=1.0)


	#=========== History output  ============#
	M.rootAssembly.regenerate()

	#Delete default history output
	del M.historyOutputRequests['H-Output-1']

	#Create history output for energies
	M.HistoryOutputRequest(name='Energy', 
		createStepName=stepName, variables=('ALLIE', 'ALLKE', 'ALLWK'),)



	#=========== Loads  ============#
	# Gravity
	M.Gravity(comp2=-9800.0, createStepName=stepName, 
	    distributionType=UNIFORM, field='', name='Gravity')

	#LL
	LL=LL_kN_m * 1.0e-3   #N/mm^2
	addSlabLoad(M, x, z, y, stepName, load = LL)

	M.rootAssembly.regenerate()


	#=========== Save and run  ============#
	
	#Save model
	mdb.saveAs(pathName = mdbName + '.cae')

	#Create job
	mdb.Job(model=modelName, name=modelName,
	    numCpus=cpus)

	#Run job
	if runStatic:
		runJob(modelName)
		#Write CPU time to file
		readMsgFile(modelName, 'results.txt')


	#=========== Post proccesing  ============#
	if staticPost:

		print 'Post processing...'

		#Clear plots
		for plot in session.xyPlots.keys():
			del session.xyPlots[plot]

		#=========== Contour  ============#
		countourPrint(modelName, defScale, printFormat)

		#=========== XY  ============#
		xyEnergyPrint(modelName, printFormat)

		#=========== Animation  ============#
		animate(modelName, defScale, frameRate= 1)
		

		print '   done'



















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
	

def fixReportFile(reportFile, plotName, modelName):
	'''
	Creates a tab file froma stupid report file

	reportFile = name of report file to fix
	plotName   = what is plottes
	modelName    = name of job
	'''
	
	fileName = 'xyData_'+plotName+'_'+modelName+'.txt'
	with open(reportFile, 'r') as f:
	    lines = f.readlines()

	with open(fileName, 'w') as f:
	    for line in lines:
	        lst = line.lstrip().rstrip().split()
	        if lst:
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