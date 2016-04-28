oldMod = modelName

modelName = 'Freq'
#Copy model
mdb.Model(name=modelName, objectToCopy=mdb.models[oldMod])

M=mdb.models[modelName]

#Delete static step
del M.steps['staticStep']

#Create Frequency step
M.FrequencyStep(name=modelName, numEigen=10, previous=
    'Initial')

#Create Frequency job
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model=modelName, modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name=modelName, nodalOutputPrecision=SINGLE, 
    numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=
    ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
