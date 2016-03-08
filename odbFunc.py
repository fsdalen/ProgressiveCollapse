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

def getMaxVal(odbName,elsetName, var, stepName, var_invariant):
	""" Returns value and object with max of a variable.
	"""
	elset = elemset = None
	region = "over the entire model"
	odb = open_odb(odbName)
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

	#Initialize maximum values
	maxVal = -0.1
	maxElem = 0
	maxStep = "_None_"
	maxFrame = -1
	var = 'S'
	isVarPresent = 0
	step = odb.steps[stepName]
	maxVal = -1.0e20
	_max=None
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
				if ( val > maxVal):
					_max = varValue
					maxVal = val
					#maxElem = varValue.elementLabel
					#maxInst = varValue.instance.name
					#maxFrame = frame.incrementNumber
		else:
			raise ValueError('Field output does not have field %s' % (results_field,))
	return (maxVal, _max)

