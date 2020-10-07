def high_level_line(file, num, x1, y1, x2, y2):
    import math

    distance = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y1 - y2, 2))

    file.write(f"#{num}=COMPOSITE_CURVE_SEGMENT(.CONTINUOUS.,.T.,#{num+1});\n")
    file.write(
        f"#{num+1}=TRIMMED_CURVE('',#{num+2},(PARAMETER_VALUE(0.0)),(PARAMETER_VALUE({distance})),.T.,.UNSPECIFIED.);\n"
    )
    file.write(f"#{num+2}=LINE('',#{num+3},#{num+4});\n")
    file.write(f"#{num+3}=CARTESIAN_POINT('',({x1},{y1},0.0));\n")
    file.write(f"#{num+4}=VECTOR('',#{num+5},1.0);\n")
    file.write(f"#{num+5}=DIRECTION('',({x2-x1},{y2-y1},0.0));\n")

    return num


def header(file):
    file.write(
        """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('STEP AP214'),'1');
FILE_NAME('hexagon.stp','2020-07-20T18:51:28',(' '),(' '),'Spatial InterOp 3D',' ',' ');
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
#13=GEOMETRICALLY_BOUNDED_SURFACE_SHAPE_REPRESENTATION('1',(#24,#25),#5);
#16=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.0E-06),#18,'','');
#18= (CONVERSION_BASED_UNIT('MILLIMETRE',#28)LENGTH_UNIT()NAMED_UNIT(#31));
#19= (NAMED_UNIT(#33)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.));
#20= (NAMED_UNIT(#33)SOLID_ANGLE_UNIT()SI_UNIT($,.STERADIAN.));
#22=PRODUCT('1','','PART--DESC',(#39));
#23=PRODUCT_DEFINITION('','NONE',#40,#1);
#24=GEOMETRIC_SET('1',(#41));
#25=AXIS2_PLACEMENT_3D('',#42,#43,#44);
#28=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.0),#45);
#31=DIMENSIONAL_EXPONENTS(1.0,0.0,0.0,0.0,0.0,0.0,0.0);
#33=DIMENSIONAL_EXPONENTS(0.0,0.0,0.0,0.0,0.0,0.0,0.0);
#39=PRODUCT_CONTEXT('',#9,'mechanical');
#40=PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE(' ','NONE',#22,.NOT_KNOWN.);
#42=CARTESIAN_POINT('',(0.0,0.0,0.0));
#43=DIRECTION('',(0.0,0.0,1.0));
#44=DIRECTION('',(1.0,0.0,0.0));
#45= (NAMED_UNIT(#31)LENGTH_UNIT()SI_UNIT(.MILLI.,.METRE.));"""
    )
    file.write("\n")
    return 46  # next line number


def footer(file):
    file.write("ENDSEC;\n")
    file.write("END-ISO-10303-21;\n")