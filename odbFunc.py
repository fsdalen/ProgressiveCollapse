from odbAccess import *
from sys import exit
import os



############################################################
############################################################
###############	  	Open ODB				################
############################################################
############################################################

def open_odb(odbPath):
	""" Enter odbPath (with or without extension) and get upgraded (if necesarly)
	odb = openOdb(odbPath)
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

	
	
############################################################
############################################################
###############	  	Get max value			################
############################################################
############################################################

def getMaxVal(odbName,elsetName, result):
    """ Print max mises location and value given odbName
        and elset(optional)
		elsetName = None will give maxval from entire model
    """
    elset = elemset = None
    region = "over the entire model"
    open_odb(odbName)
    assembly = odb.rootAssembly

    """ Check to see if the element set exists
        in the assembly
    """
    if elsetName:
        try:
            elemset = assembly.elementSets[elsetName]
            region = " in the element set : " + elsetName;
        except KeyError:
            print 'An assembly level elset named %s does' \
                   'not exist in the output database %s' \
                   % (elsetName, odbName)
            odb.close()
            exit(0)
            
    """ Initialize maximum values """
    maxMises = -0.1
    maxElem = 0
    maxStep = "_None_"
    maxFrame = -1
    Stress = 'S'
    isStressPresent = 0
    for step in odb.steps.values():
        print 'Processing Step:', step.name
        for frame in step.frames:
            allFields = frame.fieldOutputs
            if (allFields.has_key(Stress)):
                isStressPresent = 1
                stressSet = allFields[Stress]
                if elemset:
                    stressSet = stressSet.getSubset(
                        region=elemset)      
                for stressValue in stressSet.values:                
                    if (stressValue.mises > maxMises):
                        maxMises = stressValue.mises
                        maxElem = stressValue.elementLabel
                        maxStep = step.name
                        maxFrame = frame.incrementNumber
    if(isStressPresent):
        print 'Maximum von Mises stress %s is %f in element %d'%(
            region, maxMises, maxElem)
        print 'Location: frame # %d  step:  %s '%(maxFrame,maxStep)
    else:
        print 'Stress output is not available in' \
              'the output database : %s\n' %(odb.name)
    
    """ Close the output database before exiting the program """
    odb.close()

