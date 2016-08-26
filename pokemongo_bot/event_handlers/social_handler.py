# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
import thread
import paho.mqtt.client as mqtt
import Geohash
import errno
import json
import time

from socket import error as socket_error
DEBUG_ON = False
class MyMQTTClass:
    def __init__(self, bot, clientid=None):
        self.bot = bot
        self.client_id = clientid
        self.bot.mqtt_pokemon_list = []
        self._mqttc = None
    def mqtt_on_connect(self, mqttc, obj, flags, rc):
        if DEBUG_ON:
            print "rc: "+str(rc)
    def mqtt_on_message(self, mqttc, obj, msg):
        #msg.topic+" "+str(msg.qos)+" "+str(msg.payload)]
        pokemon = json.loads(msg.payload)
        if DEBUG_ON:
            print 'on message: {}'.format(pokemon)
        if pokemon and 'encounter_id' in pokemon:
            new_list = [x for x in self.bot.mqtt_pokemon_list if x['encounter_id'] is pokemon['encounter_id']]
            if not (new_list and len(new_list) > 0):
                self.bot.mqtt_pokemon_list.append(pokemon)
    def on_disconnect(self,client, userdata, rc):
        if DEBUG_ON:
            print 'on_disconnect'
            if rc != 0:
                print("Unexpected disconnection.")
    def mqtt_on_publish(self, mqttc, obj, mid):
        if DEBUG_ON:
            print "mid: "+str(mid)
    def mqtt_on_subscribe(self, mqttc, obj, mid, granted_qos):
        if DEBUG_ON:
            print "Subscribed: "+str(mid)+" "+str(granted_qos)
    #def mqtt_on_log(self, mqttc, obj, level, string):
    #    print string
    def publish(self, channel, message):
        if self._mqttc:
            self._mqttc.publish(channel, message)
    def connect_to_mqtt(self):
        try:
            if DEBUG_ON:
                print 'connect again'
            self._mqttc = mqtt.Client(None)
            if self._mqttc:
                self._mqttc.on_message = self.mqtt_on_message
                self._mqttc.on_connect = self.mqtt_on_connect
                self._mqttc.on_subscribe = self.mqtt_on_subscribe
                self._mqttc.on_publish = self.mqtt_on_publish
                self._mqttc.on_disconnect = self.on_disconnect

                self._mqttc.connect("broker.pikabot.org", 1883, 60)
                # Enable this line if you are doing the snip code, off stress
                self._mqttc.subscribe("pgo/#", 1)
                # self._mqttc.loop_start()
        except TypeError:
            print 'Connect to mqtter error'
            return
    def run(self):
        while True:
            self._mqttc.loop_forever(timeout=30.0, max_packets=100, retry_first_connection=False)
            print 'Oops disconnected ?'
            time.sleep(20)
class SocialHandler(EventHandler):
    def __init__(self, bot):
        self.bot = bot
        self.mqttc = None
    def handle_event(self, event, sender, level, formatted_msg, data):
        if self.mqttc is None:
            if DEBUG_ON:
                print 'need connect'
            try:
                self.mqttc = MyMQTTClass(self.bot, self.bot.config.client_id)
                self.mqttc.connect_to_mqtt()
                self.bot.mqttc = self.mqttc
                thread.start_new_thread(self.mqttc.run)
            except socket_error as serr:
                #if serr.errno == errno.ECONNREFUSED:
                    # ECONNREFUSED
                self.mqttc = None
                return
        #sender_name = type(sender).__name__
        #if formatted_msg:
        #    message = "[{}] {}".format(event, formatted_msg)
        #else:
            #message = '{}: {}'.format(event, str(data))
        if event == 'catchable_pokemon':
            #self.mqttc.publish("pgomapcatch/all", str(data))
            #print data
            if 'pokemon_id' in data:
                #self.mqttc.publish("pgomapcatch/all/catchable/"+str(data['pokemon_id']), str(data))
                # precision=4 mean 19545 meters, http://stackoverflow.com/questions/13836416/geohash-and-max-distance
                #geo_hash = Geohash.encode(data['latitude'], data['longitude'], precision=4)
                #self.mqttc.publish("pgomapgeo/"+geo_hash+"/"+str(data['pokemon_id']), str(data['latitude'])+","+str(data['longitude'])+","+str(data['encounter_id'])+","+str(data['pokemon_id'])+","+str(data['expiration_timestamp_ms'])+","+str(data['pokemon_name']))
                #{u'pokemon_id': 13, u'expiration_timestamp_ms': 1472017713812L, u'longitude': 4.897220519201337, u'latitude': 52.33937206069979, u'spawn_point_id': u'47c60a241ad', u'encounter_id': 13653280540966083917L}
                data_string = "%s, %s, %s, %s, %s" % (str(data['latitude']), str(data['longitude']), str(data['pokemon_id']), str(data['expiration_timestamp_ms']), str(data['pokemon_name']))
                self.mqttc.publish("pgomapcatch/all/catchable/" + str(data['pokemon_id']), data_string)
                json_data = json.dumps(data)
                self.mqttc.publish("pgo/all/catchable/"+str(data['pokemon_id']), json_data)

            #print 'have catchable_pokemon'
            #print message
