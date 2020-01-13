import todoist
import time
import shelve
import paho.mqtt.client as mqtt
import json
import logging
import os

TOPIC = os.environ['MQTT_TOPIC']

api = todoist.TodoistAPI(os.environ['TODOIST_API_KEY'])

mqtt_client = mqtt.Client()
mqtt_client.loop_start()
mqtt_client.connect(os.environ['MQTT_BROKER'])

logging.basicConfig(level='INFO')
logger = logging.getLogger()


class EventGetter:
    def __init__(self):
        self._logger = logger.getChild('EventGetter')
        self._data = shelve.open('eventgetter_shelve')
        if 'last_event' not in self._data:
            self._data['last_event'] = -1
        self._logger.info('Loaded last_event %d', self._data['last_event'])

    def get_events(self):
        activity = api.activity.get()
        yield from (x for x in activity['events'][::-1] if x['id'] > self._data['last_event'])
        self._data['last_event'] = activity['events'][0]['id']
        self._logger.info('Emitted events up to %d', self._data['last_event'])


eg = EventGetter()
while True:
    for event in eg.get_events():
        logger.info('Publishing event %d', event['id'])
        mqtt_client.publish(TOPIC, json.dumps(event), qos=1)
    time.sleep(10)
