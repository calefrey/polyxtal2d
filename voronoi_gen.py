upper_x = 10
upper_y = 10
distance = 0.05

from utils.abaqus_macro_writer import line_writer
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import random, os

points = []
for i in range(0, upper_x):
    # i = i + random.gauss(0,.5)
    for j in range(0, upper_y):
        if i % 2:
            j = j + 0.5
        points.append([i, j])
        plt.plot([i], [j], "b.")

plt.axis("square")
plt.xlim(0, upper_x)
plt.ylim(0, upper_y)
plt.show()

vor = Voronoi(points)

# display original voronoi boundaries
fig = voronoi_plot_2d(vor)
plt.axis("square")
plt.xlim(0, upper_x)
plt.ylim(0, upper_y)
plt.show()

from utils import bisector_scale, polygon_writer, header, process_lines, set_assigner
from collections import defaultdict
vertex_array = defaultdict(list) #dict of lists
grain_array = defaultdict(list)
grain_centers = []
for r_idx, region in enumerate(vor.regions):
    if not -1 in region and len(region) == 6: #bounded with 6 sides
        for i in range(2,len(region)+2):
            i = i%len(region) #wrap around 
            vertex_id = region[i-1]
            p1 = vor.vertices[region[i-2]] #neighboring point on the grain
            p2 = vor.vertices[vertex_id] #point we're interested in
            p3 = vor.vertices[region[i]] #other neighboring point
            new_point = bisector_scale(p1,p2,p3,distance)
            vertex_array[vertex_id].append(new_point) # {vertex_id:{grain_id: [new_point.x, new_point.y]}}
            grain_array[r_idx].append(new_point) #{grain_id:[point1]}
        centerx = sum([vor.vertices[p][0] for p in region])/6
        centery = sum([vor.vertices[p][1] for p in region])/6
        grain_centers.append([centerx,centery])
        plt.plot(centerx,centery,"b.")

try:
    os.remove('abaqus/output.py') #remove old version if it exists
except OSError:
    pass

with open('abaqus/output.py','a') as file:
    header(file,[upper_x,upper_y])
    for grain in grain_array.values():
        plt.fill(*zip(*grain))
        polygon_writer(file,grain)

    for vertex in vertex_array.values():
        for i in range(1,len(vertex)+1):
            i = i%len(vertex) #wrap around 
            p1 = vertex[i-1]
            p2 = vertex[i]
            if ((p1[1]-p2[1])/(p1[0]-p2[0]) < .6) and (p1[1]-p2[1])/(p1[0]-p2[0]) > .5 and len(vertex)==3: #slope of section we don't want is ~.6, but only remove it if there's 3 partitions
                pass
            else:
                line_writer(file,p1,p2)
                plt.plot(*zip(p1,p2))
    process_lines(file)
    set_assigner(file,grain_centers,"Grains")
    
plt.axis("square")
plt.xlim(0, upper_x)
plt.ylim(0, upper_y)
plt.show()