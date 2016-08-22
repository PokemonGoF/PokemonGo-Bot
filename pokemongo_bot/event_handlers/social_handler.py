# -*- coding: utf-8 -*-
from pokemongo_bot.event_manager import EventHandler
import thread
import paho.mqtt.client as mqtt
class MyMQTTClass:
    def __init__(self, clientid=None):
        self._mqttc = mqtt.Client(clientid)
        self._mqttc.on_message = self.mqtt_on_message
        #self._mqttc.on_connect = self.mqtt_on_connect
        #self._mqttc.on_publish = self.mqtt_on_publish
        #self._mqttc.on_subscribe = self.mqtt_on_subscribe
    #def mqtt_on_connect(self, mqttc, obj, flags, rc):
        #print "rc: "+str(rc)
    def mqtt_on_message(self, mqttc, obj, msg):
        print msg.topic+" "+str(msg.qos)+" "+str(msg.payload)
    #def mqtt_on_publish(self, mqttc, obj, mid):
        #print "mid: "+str(mid)
    #def mqtt_on_subscribe(self, mqttc, obj, mid, granted_qos):
    #    print "Subscribed: "+str(mid)+" "+str(granted_qos)
    #def mqtt_on_log(self, mqttc, obj, level, string):
    #    print string
    def publish(self, channel, message):
        self._mqttc.publish(channel, message)
    def connect_to_mqtt(self):
        self._mqttc.connect("test.mosca.io", 1883, 60)
        self._mqttc.subscribe("pgomapcatch/#", 0)
    def run(self):
        self._mqttc.loop_forever()
class SocialHandler(EventHandler):
    def __init__(self, bot):
        self.bot = bot
        self.mqttc = MyMQTTClass()
        self.mqttc.connect_to_mqtt()
        thread.start_new_thread(self.mqttc.run)
    def handle_event(self, event, sender, level, formatted_msg, data):
        #sender_name = type(sender).__name__
        if formatted_msg:
            message = "[{}] {}".format(event, formatted_msg)
        else:
            message = '{}: {}'.format(event, str(data))
        if event == 'catchable_pokemon':
            #self.mqttc.publish("pgomapcatch/all", str(data))
            print data
            if data['pokemon_id']:
                #self.mqttc.publish("pgomapcatch/all/catchable/"+str(data['pokemon_id']), str(data))
                self.mqttc.publish("pgomapcatch/all/catchable/"+str(data['pokemon_id']), str(data['latitude'])+","+str(data['longitude'])+","+str(data['encounter_id']))

            #print 'have catchable_pokemon'
            print message
