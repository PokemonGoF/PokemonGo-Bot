import time
from math import ceil

import haversine
import polyline

from polyline_generator import Polyline

a = Polyline((47.1706378, 8.5167405), (47.1700271, 8.518072999999998), 100)
print(a.points)
print(a.polyline_elevations)
print('Walking polyline: ', a.polyline)
print('Encoded level: ','B'*len(a.points))
print('Initialted with speed: ', a.speed, 'm/s')
print('Walking time: ', ceil(sum([haversine.haversine(*x)*1000/a.speed for x in a.walk_steps(a.points)])), ' sec.')
generated_polyline = []
print(a.points[-1])
while a.points[-1] != a.get_pos():
    pos = [a.get_pos()]
    generated_polyline += pos
    print(pos, a.get_alt())
    time.sleep(0.1)
else:
    pos = [a.get_pos()]
    print(pos, a.get_alt())
    generated_polyline += pos
    print("We have reached our destination.")
print(polyline.encode(generated_polyline))
print('Encoded level: ','B'*len(generated_polyline))
print('Verify at: ', 'https://developers.google.com/maps/documentation/utilities/polylineutility')
