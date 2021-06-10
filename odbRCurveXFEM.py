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
import math
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
    
    """geometry, NEED TO CHANGE TO INPUT QUANTITIES"""
    x0 = 0
    a0 = 10   
    L = 40
    w = a0 + L
    

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
    """Loop over steps"""
    a = []
    K = []
    for step in odb.steps.values():
        print 'Processing Step:', step.name
        """ Loop over frames """
        for frame in step.frames:
            """ load stuff """
            allFields = frame.fieldOutputs
            xfemStatus = allFields['STATUSXFEM']
            coords = allFields['COORD'].getSubset(position=CENTROID)
            statusArr = [];
            xArr = [];
            """ Find the crack tip, assumes it is growing to the LEFT """
            for s in xfemStatus.values:
                statusArr.insert(s.elementLabel-1,s.data)
                """print '%f '%(statusArr[s.elementLabel-1])"""
                
            for x in coords.values:
                xArr.insert(x.elementLabel-1,x.data[0])
                """print '%d '%(x.elementLabel-1)"""

            tipPos = x0
            maxElem = 0
            for i in range(len(xArr)):
                if (statusArr[i] > 0.999999 and xArr[i] < tipPos):
                    maxElem = i+1
                    tipPos = xArr[i]
            thisa = (x0-tipPos)+a0
            a.insert(frame.incrementNumber,thisa)
            
            """ Determine the applied stress and SIF """
            top = assembly.nodeSets['TOP']
            rf = allFields['RT'].getSubset(region=top)
            ftot = 0
            for f in rf.values:
                ftot = ftot + f.data[1]
            stress = ftot/w
            """ SIF solution from """
            xval = thisa/w
            alpha = (1.12 - 0.561*xval - 0.205*xval**2 + 0.471*xval**3 - 0.190*xval**4)/sqrt(1-xval)
            """xval = a[frame.incrementNumber]/2/w"""
            """alpha = 1.12 - 0.23*xval + 10.55*xval**2 - 21.71*xval**3 + 30.38*xval**4"""
            
            
            thisK = alpha*stress*sqrt(math.pi*thisa)
            K.insert(frame.incrementNumber,thisK)

            print 'Increment %d: Crack tip is in element %d, a = %f, K = %f'%(
            frame.incrementNumber,maxElem,thisa,thisK)
        

    """ Write the R-curve to a text file """
    Ninc = len(a)
    with open('R_curve', 'w') as f:
        for i in range(Ninc):
            f.write("%f %f\n" % (a[i],K[i]))
    
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
    