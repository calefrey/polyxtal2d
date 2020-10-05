def header(file):
    file.write(
        """
    ISO-10303-21;
    HEADER;
    FILE_DESCRIPTION(('STEP AP214'),'1');
    FILE_NAME('test2.stp','2020-08-25T21:14:18',(' '),(' '),'Spatial InterOp 3D',' ',' ');
    FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));
    ENDSEC;
    DATA;
    #1=PRODUCT_DEFINITION_CONTEXT('',#9,'design');
    #2=APPLICATION_PROTOCOL_DEFINITION('INTERNATIONAL STANDARD','automotive_design',1994,#9);
    #3=PRODUCT_CATEGORY_RELATIONSHIP('NONE','NONE',#10,#11);
    #4=SHAPE_DEFINITION_REPRESENTATION(#12,#13);
    #5= (GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#16))GLOBAL_UNIT_ASSIGNED_CONTEXT((#18,#19,#20))REPRESENTATION_CONTEXT('NONE','WORKSPACE'));
    #9=APPLICATION_CONTEXT(' ');
    #10=PRODUCT_CATEGORY('part','NONE');
    #11=PRODUCT_RELATED_PRODUCT_CATEGORY('detail',' ',(#22));
    #12=PRODUCT_DEFINITION_SHAPE('NONE','NONE',#23);
    #13=MANIFOLD_SURFACE_SHAPE_REPRESENTATION('1',(#24,#25),#5);
    #16=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.0E-06),#18,'','');
    #18= (CONVERSION_BASED_UNIT('MILLIMETRE',#28)LENGTH_UNIT()NAMED_UNIT(#31));
    #19= (NAMED_UNIT(#33)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.));
    #20= (NAMED_UNIT(#33)SOLnum_ANGLE_UNIT()SI_UNIT($,.STERADIAN.));
    #22=PRODUCT('1','','PART--DESC',(#39));
    #23=PRODUCT_DEFINITION('','NONE',#40,#1);
    #24=SHELL_BASED_SURFACE_MODEL('1',(#41));
    #25=AXIS2_PLACEMENT_3D('',#42,#43,#44);
    #28=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.0),#45);
    #31=DIMENSIONAL_EXPONENTS(1.0,0.0,0.0,0.0,0.0,0.0,0.0);
    #33=DIMENSIONAL_EXPONENTS(0.0,0.0,0.0,0.0,0.0,0.0,0.0);
    #39=PRODUCT_CONTEXT('',#9,'mechanical');
    #40=PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE(' ','NONE',#22,.NOT_KNOWN.);
    #41=CLOSED_SHELL('',(#46,#47,#48,#49,#50));
    #42=CARTESIAN_POINT('',(0.0,0.0,0.0));
    #43=DIRECTION('',(0.0,0.0,1.0));
    #44=DIRECTION('',(1.0,0.0,0.0));
    #45= (NAMED_UNIT(#31)LENGTH_UNIT()SI_UNIT(.MILLI.,.METRE.));
    """
    )
    file.write("\n")
    return 46  # next line


# 46=FACE_SURFACE('',(#52,#53,#54,#55,#56),#57,.T.);
# 52=FACE_BOUND('',#66,.T.);
# 66=EDGE_LOOP('',(#80,#81,#82,#83));
# 80=ORIENTED_EDGE('',*,*,#141,.T.);
# 141=EDGE_CURVE('',#166,#167,#168,.T.);
# 166=VERTEX_POINT('',#216);
# 216=CARTESIAN_POINT('',(5.0,22.5,0.0));
# 167=VERTEX_POINT('',#217);
# 217=CARTESIAN_POINT('',(-63.75,22.5,0.0));
# 168=LINE('',#218,#219);
# 218=CARTESIAN_POINT('',(5.0,22.5,0.0));
# 219=VECTOR('',#291,1.0);
# 291=DIRECTION('',(-1.0,0.0,0.0));
# 81=ORIENTED_EDGE('',*,*,#142,.T.);
# 142=EDGE_CURVE('',#167,#169,#170,.T.);
# 167=VERTEX_POINT('',#217);
# 217=CARTESIAN_POINT('',(-63.75,22.5,0.0));
# 169=VERTEX_POINT('',#220);
# 220=CARTESIAN_POINT('',(-63.75,-2.5,0.0));
# 170=LINE('',#221,#222);
# 221=CARTESIAN_POINT('',(-63.75,22.5,0.0));
# 222=VECTOR('',#292,1.0);
# 292=DIRECTION('',(0.0,-1.0,0.0));
# 82=ORIENTED_EDGE('',*,*,#143,.T.);
# 143=EDGE_CURVE('',#169,#171,#172,.T.);
# 169=VERTEX_POINT('',#220);
# 220=CARTESIAN_POINT('',(-63.75,-2.5,0.0));
# 171=VERTEX_POINT('',#223);
# 223=CARTESIAN_POINT('',(5.0,-2.5,0.0));
# 172=LINE('',#224,#225);
# 224=CARTESIAN_POINT('',(-63.75,-2.5,0.0));
# 225=VECTOR('',#293,1.0);
# 293=DIRECTION('',(1.0,0.0,0.0));


class CARTESIAN_POINT:
    def __init__(self, x, y, num):
        self.x = x
        self.y = y
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=CARTESIAN_POINT('',({self.x},{self.y},0.0));\n")
        return self.num + 1


class VERTEX_POINT:
    def __init__(self, pt: CARTESIAN_POINT, num):
        self.pt = pt
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=VERTEX_POINT('',#{self.pt.num});\n")
        return self.num + 1


class DIRECTION:
    def __init__(self, dx, dy, num):
        self.dx = dx
        self.dy = dy
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=DIRECTION('',({self.dx},{self.dy},0.0));\n")
        return self.num + 1


class VECTOR:
    def __init__(self, direction: DIRECTION, num):
        self.direction = direction
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=VECTOR('',#{self.direction.num},1.0);\n")
        return self.num + 1


class AXIS:
    def __init__(self, num):
        self.pt = pt
        self.num = num

    def write(self, file):
        file.write(
            f"#{self.num}=AXIS2_PLACEMENT_3D('',#{self.num+1},#{self.num+2},#{self.num+3});\n"
        )
        file.write(f"#{self.num+1}=CARTESIAN_POINT('',(0.0,0.0,0.0));\n")
        file.write(f"#{self.num+2}=DIRECTION('',(0.0,0.0,1.0));\n")
        file.write(f"#{self.num+3}=DIRECTION('',(1.0,0.0,0.0));\n")
        return self.num + 4


class PLANE:
    def __init__(self, axis: AXIS, num):
        self.axis = axis
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=PLANE('',#{self.axis.num});\n")
        return self.num + 1


class LINE:
    def __init__(self, pt: CARTESIAN_POINT, vector: VECTOR, num):
        self.vector = vector
        self.pt = pt
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=LINE('',#{self.pt.num},#{self.vector.num});\n")
        return self.num + 1


class EDGE_CURVE:
    def __init__(self, p1: VERTEX_POINT, p2: VERTEX_POINT, line: LINE, num):
        self.p1 = p1
        self.p2 = p2
        self.line = line
        self.num = num

    def write(self, file):
        file.write(
            f"#{self.num}=EDGE_CURVE('',#{self.p1.num},#{self.p2.num},#{self.line.num},.T.);\n"
        )
        return self.num + 1


class ORIENTED_EDGE:
    def __init__(self, ec: EDGE_CURVE, num):
        self.ec = ec
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=ORIENTED_EDGE('',*,*,#{self.ec.num},.T.);\n")
        return self.num + 1


class EDGE_LOOP:
    def __init__(self, oriented_edges: list, num):
        self.edges = oriented_edges
        self.num = num

    def write(self, file):
        file.write(
            f"#{self.num}=EDGE_LOOP('',({','.join([f'#{e.num}' for e in self.edges])}));\n"
        )
        return self.num + 1


class FACE_BOUND:
    def __init__(self, edge_loop: EDGE_LOOP, num):
        self.loop = edge_loop
        self.num = num

    def write(self, file):
        file.write(f"#{self.num}=FACE_BOUND('',#{self.loop.num},.T.);\n")
        return self.num + 1


class FACE_SURFACE:
    def __init__(self, face_bound: FACE_BOUND, plane: PLANE, num):
        self.face_bound = face_bound
        self.plane = plane
        self.num = num

    def write(self, file):
        file.write(
            f"#{self.num}=FACE_SURFACE('',(#{self.face_bound.num}),#{self.plane.id},.T.);\n"
        )
        return self.num + 1


from utils.grain_class import grain


def part_writer(g: grain, file, n):
    oriented_edges = []
    for i in range(1, len(g.vertices) + 1):
            i = i % len(g.vertices)  # wrap around the list 
            # vertices[i] and vertices[i-1] available
            x1,y1 = g.vertices[i-1]
            x2,y2 = g.vertices[i]
            file.write(f"#{n+0}=VERTEX_POINT('',#{n+1});\n")
            file.write(f"#{n+1}=CARTESIAN_POINT('',({x1},{y1},0.0));\n")
            file.write(f"#{n+2}=VERTEX_POINT('',#{n+3});\n")
            file.write(f"#{n+3}=CARTESIAN_POINT('',({x2},{y2},0.0));\n")
            file.write(f"#{n+4}=VECTOR('',#{n+5},1.0);\n")
            file.write(f"#{n+5}=DIRECTION('',({x1-x2},{y1-y2},0.0));\n")
            file.write(f"#{n+6}=LINE('',#{n+1},#{n+4});\n")
            file.write(f"#{n+7}=EDGE_CURVE('',#{n+0},#{n+2},#{n+6},.T.);\n")
            file.write(f"#{n+8}=ORIENTED_EDGE('',*,*,#{n+7},.T.);\n")
            oriented_edges.append(n+8)
            n += 8 #keep the rest in line
    
    file.write(f"#{n}=EDGE_LOOP('',({','.join([f'#{x}' for x in oriented_edges])}));\n") #comma separated list of the oriented edges, with #s in front
    file.write(f"#{n+1}=FACE_BOUND('',#{n},.T.);\n")
    file.write(
            f"#{n+2}=FACE_SURFACE('',(#{n+1}),#{plane_id},.T.);\n"
        )
    return n+3