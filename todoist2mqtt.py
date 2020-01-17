# Copyright (c) 2020, Philipp Tölke
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import todoist
import time
import shelve
import paho.mqtt.client as mqtt
import json
import logging
import os

TOPIC = os.environ.get('MQTT_TOPIC', 'todoist/activity')

api = todoist.TodoistAPI(os.environ['TODOIST_API_KEY'])

mqtt_client = mqtt.Client()
mqtt_client.loop_start()
mqtt_client.connect(os.environ.get('MQTT_BROKER', '127.0.0.1'))

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
    time.sleep(os.environ.get('SLEEP_TIME', 60))
