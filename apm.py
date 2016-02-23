#====================================================================#
#							Inputs 									 #
#====================================================================#
#Natural frequency
freq = 200






#====================================================================#
#							APM 									 #
#====================================================================#



#Create new model
mdb.Model(name='DynamicAPM', objectToCopy=mdb.models['Static'])
M = mdb.models['DynamicAPM']
#M.setValues(restartJob='staticJob', restartStep='Static')


#Delete old step
del M.steps['Static']

#Create Implicit Dynamic Step
stepName = 'Dynamic'
M.ImplicitDynamicsStep(name=stepName, nlgeom=nlg, previous='Initial')


#Delete column
#del M.rootAssembly.features['Column_A2-1']

#Redefine LL
for a in range(len(alph)-1):
	for n in range(len(numb)-1):
		for e in range(len(etg)):
			inst = "Slab_" + alph[a]+numb[n]+"-"+etg[e]
			M.SurfaceTraction(createStepName=stepName, 
				directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
				distributionType=UNIFORM, field='', follower=OFF,
				localCsys=None, magnitude= LL, name="Slab_" + alph[a]+numb[n]+"-"+etg[e],
				region= M.rootAssembly.instances[inst].surfaces['Surf'],
				traction=GENERAL)

#Import initial conditions
#This should be put in a loop
# M.InitialState(createStepName='Initial', endIncrement=
#     STEP_END, endStep=LAST_STEP, fileName='staticJob', instances=(
#     M.rootAssembly.instances['Column_A1-1'], 
#     M.rootAssembly.instances['Column_B1-1'], 
#     M.rootAssembly.instances['Column_B2-1'], 
#     M.rootAssembly.instances['Beam_A1-B1-1'], 
#     M.rootAssembly.instances['Beam_A2-B2-1'], 
#     M.rootAssembly.instances['Beam_A1-A2-1'], 
#     M.rootAssembly.instances['Beam_B1-B2-1'], 
#     M.rootAssembly.instances['Slab_A1-1']), name=
#     'Predefined Field-1', updateReferenceConfiguration=OFF)


#1/10 of natural period
period = 1.0/freq

#Create amplitude
M.SmoothStepAmplitude(data=((0.0, 1.0), (period, 0.0)), 
    name='Amp-1', timeSpan=STEP)

#Get force from static analysis
O=odbAccess.openOdb(path='staticJob.odb')
force = O.steps['Static'].historyRegions['Element COLUMN_A2-1.10 Node COLUMN_A2-1.11'].historyOutputs['NFORCSO3'].data[-1][1]


#Create Force
# M.ConcentratedForce(cf2=-force, createStepName='Dynamic', 
# 	distributionType=UNIFORM, field='', localCsys=None, name='Load-2', region=
# 	Region(
# 	M.rootAssembly.instances['Slab_A1-1'].vertices.findAt(
# 	((0.0, 500.0, 500.0), ), )))

#Delete old BC if applicable
# del M.boundaryConditions['Column_A2-1.col-base']

#Delete set and history output related to deleted element
#del M.rootAssembly.sets['element']
# del M.historyOutputRequests['Element']	#Not needed when static step is deleted

#Create Job
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model='DynamicAPM', modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name='dynamicJob', nodalOutputPrecision=SINGLE
    , numCpus=cpus, numDomains=2, numGPUs=0, queue=None, resultsFormat=ODB, 
    scratch='', type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
