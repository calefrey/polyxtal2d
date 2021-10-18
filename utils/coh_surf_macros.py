from functools import wraps
from os import write
from typing import List, Text, TextIO


def interaction_property(
    f: TextIO,
    prop_name: str,
    damagevalue: float,
    plastic_displacement: float,
    viscosity: float = None,
    coh_stiffness: float = 1e9,
):
    """
    Optional viscosity value, if not set the relevant statements are omitted
    """
    f.write(
        f"""
mdb.models['Model-1'].ContactProperty('{prop_name}')
mdb.models['Model-1'].interactionProperties['{prop_name}'].CohesiveBehavior(
    defaultPenalties=OFF, table=(({coh_stiffness}, {coh_stiffness}, {coh_stiffness}), ))
mdb.models['Model-1'].interactionProperties['{prop_name}'].Damage(
    initTable=(({damagevalue}, {damagevalue}, {damagevalue}), ), useEvolution=ON,
    #if there is a given viscosity include this section, and if not it'll just be blank
    evolTable=(({plastic_displacement}, ),){f', useStabilization=ON, viscosityCoef={viscosity}' if viscosity else ''})
"""
    )


def general_interaction(f: TextIO, int_name: str, global_prop_id: str):
    f.write(
        f"""
mdb.models['Model-1'].StdInitialization(name='CInit-1', openingTolerance=.006, overclosureTolerance=1.0)
mdb.models['Model-1'].ContactStd(name='{int_name}', createStepName='Initial')
mdb.models['Model-1'].interactions['{int_name}'].includedPairs.setValuesInStep(
    stepName='Initial', useAllstar=ON)
mdb.models['Model-1'].interactions['{int_name}'].contactPropertyAssignments.appendInStep(
    stepName='Initial', assignments=((GLOBAL, SELF, '{global_prop_id}'),))
mdb.models['Model-1'].interactions['{int_name}'].surfaceThicknessAssignments.appendInStep(
    stepName='Initial', assignments=((GLOBAL, 0.005, 1.0), ))
mdb.models['Model-1'].interactions['{int_name}'].initializationAssignments.appendInStep(
    stepName='Initial', assignments=((GLOBAL, SELF, 'CInit-1'), ))
"""
    )


def property_assignment(
    f: TextIO, interaction: str, prop_name: str, surf_1: str, surf_2: str
):
    """
    Individual property assignments
    """
    f.write(
        f"""
s=mdb.models['Model-1'].rootAssembly.surfaces
mdb.models['Model-1'].interactions['{interaction}'].contactPropertyAssignments.appendInStep(
    stepName='Initial', assignments=((s['{surf_1}'], s['{surf_2}'], '{prop_name}'), ))
"""
    )


def surface_maker(f: TextIO, surface_name: str, surface_points):
    """
    [[x1,y1],[x2,y2],...] as input
    """

    # final output should look like "s.findAt(((-51.138825, -2.11286, 0.0), ), ((-53.638825, -1.391173, 0.0), )"
    coords = ""
    for point in surface_points:
        coords = (
            coords + f"(({point[0]:.6f}, {point[1]:.6f}, 0.0), ), "
        )  # at least it's not {"(("+', ), ('.join([str((*x,0)) for x in points])+"))"}
        # using :.6f to round the value since findAt only supports 1e-6 precision
    f.write(
        f"""
side1Edges = s.findAt({coords})
a.Surface(side1Edges=side1Edges, name='{surface_name}')
"""
    )


def header(f: TextIO):
    f.write(
        f"""
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(0.0, 0.0), width=225.91552734375, 
    height=222.83332824707)
session.viewports['Viewport: 1'].makeCurrent()
session.viewports['Viewport: 1'].maximize()
from caeModules import *
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
session.viewports['Viewport: 1'].partDisplay.geometryOptions.setValues(
    referenceRepresentation=ON)
Mdb()
#: A new model database has been created.
#: The model "Model-1" has been created.
#: A new model database has been created.
#: The model "Model-1" has been created.
session.viewports['Viewport: 1'].setValues(displayedObject=None)
session.viewports['Viewport: 1'].partDisplay.setValues(sectionAssignments=OFF, 
    engineeringFeatures=OFF)
session.viewports['Viewport: 1'].partDisplay.geometryOptions.setValues(
    referenceRepresentation=ON)
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', 
    sheetSize=200.0)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.setPrimaryObject(option=STANDALONE)
mdb.models['Model-1'].StaticStep(maxNumInc=10000, name='Step-1', previous=
    'Initial',initialInc=0.1, maxInc=0.1)
mdb.models['Model-1'].steps['Step-1'].control.setValues(allowPropagation=OFF, 
    resetDefaultValues=OFF, discontinuous=ON)
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(variables=(
    'S', 'PE', 'PEEQ', 'PEMAG', 'LE', 'U', 'RF', 'CF', 'CSTRESS', 'CDISP', 
    'CSTATUS', 'COORD', 'CSDMG'))
"""
    )


def process_lines(f: TextIO):
    f.write(
        f"""
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=TWO_D_PLANAR, 
    type=DEFORMABLE_BODY)
p = mdb.models['Model-1'].parts['Part-1']
p.BaseShell(sketch=s)
s.unsetPrimaryObject()
p = mdb.models['Model-1'].parts['Part-1']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
del mdb.models['Model-1'].sketches['__profile__']
a = mdb.models['Model-1'].rootAssembly
a.DatumCsysByDefault(CARTESIAN)
p = mdb.models['Model-1'].parts['Part-1']
f = p.faces
p.Set(faces=f,name='All')
"""
    )


def make_instance(f: TextIO):
    f.write(
        f"""
a.Instance(name='Part-1-1', part=p, dependent=ON)
session.viewports['Viewport: 1'].assemblyDisplay.setValues(interactions=ON, 
    constraints=ON, connectors=ON, engineeringFeatures=ON)
s = a.instances['Part-1-1'].edges
"""
    )


def polygon_writer(f: TextIO, points: list):
    for i in range(1, len(points) + 1):
        i = i % len(points)  # wrap around
        p1 = points[i - 1]
        p2 = points[i]
        line_writer(f, p1, p2)


def line_writer(f: TextIO, p1: list, p2: list):
    f.write(f"s.Line(point1=({p1[0]}, {p1[1]}), point2=({p2[0]}, {p2[1]}))\n")


def mesh(f: TextIO, seed_size=0.11):
    f.write(
        f"""
elemType1 = mesh.ElemType(elemCode=CPS4, elemLibrary=STANDARD)
elemType2 = mesh.ElemType(elemCode=CPS3, elemLibrary=STANDARD)
p = mdb.models['Model-1'].parts['Part-1']
f = p.faces
pickedRegions =(f, )
p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2))
p.seedPart(size={seed_size}, deviationFactor=0.1, minSizeFactor=0.1)
p = mdb.models['Model-1'].parts['Part-1']
p.generateMesh()
"""
    )


def set_maker(f: TextIO, set_name: str, points: list):
    """
    [[x1,y1],[x2,y2],...] as input
    """
    # final output should look like "f1.findAt(((-51.138825, -2.11286, 0.0), ), ((-53.638825, -1.391173, 0.0), )"
    coords = ""
    for point in points:
        coords = (
            coords + f"(({point[0]:.6f}, {point[1]:.6f}, 0.0), ), "
        )  # at least it's not {"(("+', ), ('.join([str((*x,0)) for x in points])+"))"}
        # using :.6f to round the value since findAt only supports 1e-6 precision
    f.write(
        f"""
a = mdb.models['Model-1'].rootAssembly
f1 = a.instances['Part-1-1'].faces
faces1 = f1.findAt({coords})
a.Set(faces=faces1, name='{set_name}')
"""
    )


def encastre(f: TextIO, bc_name: str = "BC-1", threshold=1.5):
    f.write(
        f"""
f=p.faces
botfaces = []
for i in f:
    if i.getCentroid()[0][1]<{threshold}:
        # if the y value of the centroid is below the threshold consider it the bottom
        index=i.index
        botfaces.append(f[index:index+1])
p.Set(name='bottom',faces=botfaces)

a = mdb.models['Model-1'].rootAssembly
region = a.instances['Part-1-1'].sets['bottom']

mdb.models['Model-1'].EncastreBC(name='{bc_name}', createStepName='Initial', 
    region=region, localCsys=None)
"""
    )


def top_displacement(
    f: TextIO, bc_name: str = "BC-1", u1="UNSET", u2="UNSET", u3="UNSET", threshold=0.5
):
    f.write(
        f"""
f=p.faces
topfaces = []
for i in f:
    if i.getCentroid()[0][1] > {threshold}:
        # if the y value of the centroid is above the threshold consider it the top
        index=i.index
        topfaces.append(f[index:index+1])
p.Set(name='top',faces=topfaces)
a = mdb.models['Model-1'].rootAssembly
region = a.instances['Part-1-1'].sets['top']
mdb.models['Model-1'].DisplacementBC(name='{bc_name}', createStepName='Step-1', 
    region=region, u1={u1}, u2={u2}, ur3={u3})
"""
    )


def section(f: TextIO, material_name: str, modulus: float, poisson: float):
    f.write(
        f"""
mdb.models['Model-1'].Material(name='{material_name}')
mdb.models['Model-1'].materials['{material_name}'].Elastic(table=(({modulus}, {poisson}), ))
mdb.models['Model-1'].HomogeneousSolidSection(name='Section-1', 
    material='{material_name}', thickness=None)
p = mdb.models['Model-1'].parts['Part-1']
region = p.sets['All']
p = mdb.models['Model-1'].parts['Part-1']
p.SectionAssignment(region=region, sectionName='Section-1', offset=0.0, 
    offsetType=MIDDLE_SURFACE, offsetField='', 
    thicknessAssignment=FROM_SECTION)
"""
    )


def write_inp(f: TextIO, jobname: str):
    f.write(
        f"""
mdb.Job(name='{jobname}', model='Model-1', description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=1, 
    numGPUs=0)
mdb.jobs['{jobname}'].writeInput(consistencyChecking=OFF)
mdb.saveAs('{jobname}')
"""
    )
