import requests
import time
import haversine
from math import ceil
from polyline_walker import PolylineWalker
URL = 'https://maps.googleapis.com/maps/api/directions/json?origin=Poststrasse+1,Zug,CH&destination=Poststrasse+9,Zug,CH&mode=walking'
a = PolylineWalker([x['polyline']['points'] for x in  requests.get(URL).json()['routes'][0]['legs'][0]['steps']], 80)
print('Initialted with speed: ', a.speed, 'm/s')
print('Walking time: ', ceil(sum([haversine.haversine(*x)*1000/a.speed for x in a.walk_steps()])), ' sec.')
while a.points[-1] != a.get_pos()[0]:
    print(a.get_pos())
    time.sleep(0.1)
else:
    print("We have reached our destination.")
