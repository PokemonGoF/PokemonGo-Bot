import requests
import time
import haversine
import polyline
from math import ceil
from polyline_walker import PolylineWalker
URL = 'https://maps.googleapis.com/maps/api/directions/json?origin=Poststrasse+1,Zug,CH&destination=Guggiweg+7,Zug,CH&mode=walking'
a = PolylineWalker([x['polyline']['points'] for x in  requests.get(URL).json()['routes'][0]['legs'][0]['steps']], 80)
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
