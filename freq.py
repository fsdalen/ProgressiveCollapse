#Copy model
mdb.Model(name='Freq', objectToCopy=mdb.models['Static'])

#Delete static step
del mdb.models['Static'].steps['Static']

#Create Frequency step
mdb.models['Static'].FrequencyStep(name='Step-1', numEigen=10, previous=
    'Initial')

#Create Frequency job
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model='Static', modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name='freq', nodalOutputPrecision=SINGLE, 
    numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=
    ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
