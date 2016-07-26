import time
from math import ceil

import haversine
import polyline
<<<<<<< HEAD:pokemongo_bot/walkers/polyline_generator_tester.py
from math import ceil
from polyline_generator import Polyline
a = Polyline((47.1706378, 8.5167405), (47.1700271, 8.518072999999998), 100)
print(a.points)
=======

from polyline_walker import PolylineWalker

a = PolylineWalker('Poststrasse+20,Zug,CH', 'Guggiweg+7,Zug,CH', 100)
>>>>>>> 508eb404835e9abdfe1d42bad2720db11cfab1a0:pokemongo_bot/polyline_walker/polyline_tester.py
print('Walking polyline: ', a.polyline)
print('Encoded level: ','B'*len(a.points))
print('Initialted with speed: ', a.speed, 'm/s')
print('Walking time: ', ceil(sum([haversine.haversine(*x)*1000/a.speed for x in a.walk_steps()])), ' sec.')
generated_polyline = []
while a.points[-1] != a.get_pos()[0]:
    pos = a.get_pos()
    generated_polyline += pos
    print(pos)
    time.sleep(0.1)
else:
    print("We have reached our destination.")
print(polyline.encode(generated_polyline))
print('Encoded level: ','B'*len(generated_polyline))
print('Verify at: ', 'https://developers.google.com/maps/documentation/utilities/polylineutility')
