# Generate .rpy file using existing files as template, and then when you open CAE 'Run Script" and select the rpy file.


def line_writer(f, p1: list, p2: list):
    f.write(f"s1.Line(point1=({p1[0]}, {p1[1]}), point2=({p2[0]}, {p2[1]}))\n")


# #http://130.149.89.49:2080/v6.13/books/cmd/default.htm?startat=pt02ch06s06.html
# def section_assigner(f, point_on_section:list, section_name:str):
#     f.append(f"""
# faces = f.findAt((({point_on_section[0]},{point_on_section[1]}),)) #find face where the given point exists, can't overlap with other faces
# region = regionToolset.Region(faces=faces)
# p = mdb.models['Model-1'].parts['Part-1']
# p.SectionAssignment(region=region, sectionName='{section_name}', offset=0.0,
#     offsetType=MIDDLE_SURFACE, offsetField='',
#     thicknessAssignment=FROM_SECTION)
# p = mdb.models['Model-1'].parts['Part-1']
# f = p.faces
# """)


def set_assigner(f, points: list, set_name: str):
    """
    Create a set from a list of points like [[x1,y1],[x2,y2],[x3,y3]]
    """
    # example:
    # faces = f.findAt(((-2.11, -15.015, 0.0), ), ((20.889999, 13.045, 0.0), ), ((-19.333731, 13.095932, 0.0), ), ((-44.429999, 5.685, 0.0), ))
    # p.Set(faces=faces, name='Set-2')
    coords = ""
    for point in points:
        coords = coords + f"(({point[0]}, {point[1]}, 0.0), ), "
    f.write(f"faces = f.findAt({coords})\n")
    f.write(f"p.Set(faces=faces, name='{set_name}')\n")
    print("Set created")


def polygon_writer(f, points: list):
    for i in range(1, len(points) + 1):
        i = i % len(points)  # wrap around
        p1 = points[i - 1]
        p2 = points[i]
        line_writer(f, p1, p2)


def initialize(f, bounds: list):
    """
    File object and [max_x,max_y]
    """
    f.write(
        f"""
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(0.0, 0.0), width=206.67626953125, 
    height=86.9166641235352)
session.viewports['Viewport: 1'].makeCurrent()
session.viewports['Viewport: 1'].maximize()
from caeModules import *
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
#: Abaqus Warning: Keyword (dsls_license_config) must point to an existing file.
session.viewports['Viewport: 1'].partDisplay.geometryOptions.setValues(
    referenceRepresentation=ON)
Mdb()
#: A new model database has been created.
#: The model "Model-1" has been created.
session.viewports['Viewport: 1'].setValues(displayedObject=None)
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', 
    sheetSize=200.0)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.setPrimaryObject(option=STANDALONE)
s.rectangle(point1=(0.0, 0.0), point2=({bounds[0]}, {bounds[1]}))
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=TWO_D_PLANAR, 
    type=DEFORMABLE_BODY)
p = mdb.models['Model-1'].parts['Part-1']
p.BaseShell(sketch=s)
s.unsetPrimaryObject()
p = mdb.models['Model-1'].parts['Part-1']
session.viewports['Viewport: 1'].setValues(displayedObject=p)
del mdb.models['Model-1'].sketches['__profile__']
p = mdb.models['Model-1'].parts['Part-1']
f, e, d1 = p.faces, p.edges, p.datums
t = p.MakeSketchTransform(sketchPlane=f[0], sketchPlaneSide=SIDE1, origin=(0.0, 
    0.0, 0.0))
s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', 
    sheetSize=28.28, gridSpacing=0.5, transform=t)
g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
s1.setPrimaryObject(option=SUPERIMPOSE)
p = mdb.models['Model-1'].parts['Part-1']
p.projectReferencesOntoSketch(sketch=s1, filter=COPLANAR_EDGES)
#s1.sketchOptions.setValues(gridOrigin=(-5.0, -5.0))
"""
    )


def process_lines(f):
    """abaqus needs to create faces after all of these lines we just wrote"""
    f.write(
        """
p = mdb.models['Model-1'].parts['Part-1']
f = p.faces
pickedFaces = f.getSequenceFromMask(mask=('[#1 ]', ), )
e1, d2 = p.edges, p.datums
p.PartitionFaceBySketch(faces=pickedFaces, sketch=s1)
s1.unsetPrimaryObject()
del mdb.models['Model-1'].sketches['__profile__']
"""
    )
