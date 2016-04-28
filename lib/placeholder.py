#=======================================================#
#=======================================================#
#                   CPU time                            #
#=======================================================#
#=======================================================#
odb.jobData.creationTime[11:20]
odb.jobData.modificationTime[11:20]




#==============================================================#
#==============================================================#
#                    Write tab data                            #
#==============================================================#
#==============================================================#
def writeData(odbName, data, name, var1, var2, unit1, unit2):
	'''
	Takes xy data and writes to file. 
	
	odbName      = odb to read from
	data         = tuple of double tuples (or list) containing data
	name         = name of data set
	var1, var2   = name of variables
	unit1, unit2 = units of variables

	Output format of file:
	=======================
	var1_unit1	var2_unit2

	data1	data2
	data1	data2
	data1	data2
	=======================
	'''

	v1 = [x[0] for x in data]
	v2 = [x[1] for x in data]
	fileName = 'xyData_'+name+'_'+odbName+'.txt'
	with open(fileName, 'w+') as f:
		f.write(var1+'_'+unit1+'\t'+var2+'_'+unit2+'\n\n')
		for i in range(len(v1)):
			f.write('%10.6E' %(v1[i]))
			f.write('\t')
			f.write('%10.6E \n' %(v2[i]))





#==================================================================#
#==================================================================#
#              Read report file with Numpy                         #
#==================================================================#
#==================================================================#
def process_rpt(fname):

	fname = 'test.txt'

	with open(fname, 'rb') as f:
	    lines = f.readlines()

	lines_cleaned = []

	for line in lines:
	    # Strip leading and trailing whitespace
	    line_cleaned = line.lstrip().rstrip()
	    # Ignore blank lines

	    if len(line_cleaned):
	        # Check if first element is a float
	        line_cleaned = line_cleaned.split()
	        try:
	            float(line_cleaned[0])
	            lines_cleaned.append(line_cleaned)
	        except:
	            pass

	tmp = np.zeros((len(lines_cleaned),len(lines_cleaned[0])))

	for i,line in enumerate(lines_cleaned):
	    tmp[i,:] = np.array(map(float, line))

	return tmp




#======================================================================#
#======================================================================#
#                   Get max result from ODB                            #
#======================================================================#
#======================================================================#
	


def max_result(odb, result):
    result_field, result_invariant = result
    _max = -1.0e20
    for step in odb.steps.values():
        print 'Processing Step:', step.name
        for frame in step.frames:
            if frame.frameValue > 0.0:
                allFields = frame.fieldOutputs
                if (allFields.has_key(result_field)):
                    stressSet = allFields[result_field]
                    for stressValue in stressSet.values:
                        if result_invariant:
                            if hasattr(stressValue, result_invariant.lower()):
                                val = getattr(stressValue,result_invariant.lower())
                            else:
                                raise ValueError('Field value does not have invariant %s' % (result_invariant,))
                        else:
                            val = stressValue.data
                        if ( val > _max):
                            _max = val
                else:
                    raise ValueError('Field output does not have field %s' % (results_field,))
    return _max

if __name__ == '__main__':
    odb_name = sys.argv[1]
    print odb_name
    odb = open_odb(odb_name)
    max_mises = max_result(odb,('S','mises'))
    max_peeq = max_result(odb,('PEEQ',''))
    print max_mises, max_peeq




#======================================================================#
#======================================================================#
#                   Get max result from ODB                            #
#======================================================================#
#======================================================================#


"""
odbMaxMises.py
Code to determine the location and value of the maximum
von-mises stress in an output database.
Usage: abaqus python odbMaxMises.py -odb odbName
       -elset(optional) elsetName
Requirements:
1. -odb   : Name of the output database.
2. -elset : Name of the assembly level element set.
            Search will be done only for element belonging
            to this set. If this parameter is not provided,
            search will be performed over the entire model.
3. -help  : Print usage
"""

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from odbAccess import *
from sys import argv,exit
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def rightTrim(input,suffix):
    if (input.find(suffix) == -1):
        input = input + suffix
    return input
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def getMaxMises(odbName,elsetName):
    """ Print max mises location and value given odbName
        and elset(optional)
    """
    elset = elemset = None
    region = "over the entire model"
    """ Open the output database """
    odb = openOdb(odbName)
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

#==================================================================
# S T A R T
#    
if __name__ == '__main__':
    
    odbName = None
    elsetName = None
    argList = argv
    argc = len(argList)
    i=0
    while (i < argc):
        if (argList[i][:2] == "-o"):
            i += 1
            name = argList[i]
            odbName = rightTrim(name,".odb")
        elif (argList[i][:2] == "-e"):
            i += 1
            elsetName = argList[i]
        elif (argList[i][:2] == "-h"):            
            print __doc__
            exit(0)
        i += 1
    if not (odbName):
        print ' **ERROR** output database name is not provided'
        print __doc__
        exit(1)
    getMaxMises(odbName,elsetName)
    
