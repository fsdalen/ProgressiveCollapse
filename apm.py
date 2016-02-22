#====================================================================#
#							Inputs 									 #
#====================================================================#
#Natural frequency
freq = 200


#============== Related to which column to delete ==========#



#====================================================================#
#							APM 									 #
#====================================================================#

#Create new model
mdb.Model(name='DynamicAPM', objectToCopy=mdb.models['Static'])
M = mdb.models['DynamicAPM']
M.setValues(restartJob='staticJob', restartStep='Static')

#Create Implicit Dynamic Step
M.ImplicitDynamicsStep(name='Dynamic', nlgeom=nlg, previous='Static')

#Delete column
del M.rootAssembly.features['Column_A2-1']

#1/10 of natural period
period = 1.0/freq

#Create amplitude
M.SmoothStepAmplitude(data=((0.0, 1.0), (period, 0.0)), 
    name='Amp-1', timeSpan=STEP)

#Get force from static analysis
O=odbAccess.openOdb(path='staticJob.odb')
force = O.steps['Static'].historyRegions['Element COLUMN_A2-1.10 Node COLUMN_A2-1.11'].historyOutputs['NFORCSO3'].data[-1][1]


#Create Force
M.ConcentratedForce(cf2=-force, createStepName='Dynamic', 
distributionType=UNIFORM, field='', localCsys=None, name='Load-2', region=
Region(
M.rootAssembly.instances['Slab_A1-1'].vertices.findAt(
((0.0, 500.0, 500.0), ), )))

#Delete old BC if applicable
del M.boundaryConditions['Column_A2-1.col-base']

#Delete set and history output related to deleted element
del M.rootAssembly.sets['element']
del M.historyOutputRequests['Element']

#Create Job
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model='DynamicAPM', modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name='dynamicJob', nodalOutputPrecision=SINGLE
    , numCpus=cpus, numDomains=2, numGPUs=0, queue=None, resultsFormat=ODB, 
    scratch='', type=RESTART, userSubroutine='', waitHours=0, waitMinutes=0)


