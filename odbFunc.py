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

def getMaxVal(odbName,elsetName, var, stepName, var_invariant, limit):
	""" Returns list with value and object for all elements over limit
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
	#Find values over limit
	var = 'S'
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

