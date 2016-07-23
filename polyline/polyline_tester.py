import requests
import time
import haversine
from polyline_walker import PolylineWalker
URL = 'https://maps.googleapis.com/maps/api/directions/json?origin=Baar,CH&destination=Cham,CH&mode=walking'
a = PolylineWalker([x['polyline']['points'] for x in  requests.get(URL).json()['routes'][0]['legs'][0]['steps']], 2.5)
len(a.points)
while a.points:
    before = a.points[1:]
    now = a.walk()
    print(len(a.points), len(a.points))
    after = a.points[1:]
    print('Remaining ', haversine.haversine(a.points[1], now)*1000, ' m. on current polyline. ', len(a.points), ' polylines remaining.')
    print('Estimated completion time: ', (sum([haversine.haversine(*x)*1000 for x in a.walk_steps()]) / a.speed) , ' seconds.')
    if before != after:
        print('Changed polyline: ', a.polyline)
    time.sleep(1.5)

