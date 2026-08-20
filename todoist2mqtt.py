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

import datetime
import json
import logging
import os
import shelve
import time

import paho.mqtt.client as mqtt
import requests

TOPIC = os.environ.get("MQTT_TOPIC", "todoist/activity")

session = requests.Session()
session.headers.update(
    {
        "Authorization": f'Bearer {os.environ["TODOIST_API_KEY"]}',
    }
)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.loop_start()
mqtt_client.connect(os.environ.get("MQTT_BROKER", "127.0.0.1"))

logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger()


class EventGetter:
    def __init__(self):
        self._logger = logger.getChild("EventGetter")
        self._data = shelve.open("eventgetter_shelve")

    def _get_activities(self):
        response = session.get("https://api.todoist.com/api/v1/activities", timeout=30)
        if not response.ok:
            self._logger.error(
                "Activities request failed: HTTP %s %s (content-type %s): %s",
                response.status_code,
                response.reason,
                response.headers.get("Content-Type", "<none>"),
                response.text[:500],
            )
            response.raise_for_status()
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            self._logger.exception(
                "Could not decode activities response as JSON: "
                "HTTP %s %s (content-type %s, %d bytes): %s",
                response.status_code,
                response.reason,
                response.headers.get("Content-Type", "<none>"),
                len(response.content),
                response.text[:500],
            )
            raise

    def get_events(self):
        is_first_start = "last_event_id" not in self._data
        cutoff = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
            if is_first_start
            else None
        )
        last_seen = self._data.get("last_event_id", -1)
        activity = self._get_activities()
        try:
            results = activity["results"]
        except KeyError:
            self._logger.exception("Missing key in response: %s", activity)
            raise
        new_events = [
            e
            for e in results[::-1]
            if e["id"] > last_seen
            and (cutoff is None or datetime.datetime.fromisoformat(e["event_date"]) >= cutoff)
        ]
        yield from new_events
        if results:
            self._data["last_event_id"] = results[0]["id"]
            self._logger.info("Emitted events up to id %s", results[0]["id"])


eg = EventGetter()
sleep_time = int(os.environ.get("SLEEP_TIME", "60"))
while True:
    try:
        for event in eg.get_events():
            logger.info("Publishing event %d %s", event["id"], event)
            mqtt_client.publish(TOPIC, json.dumps(event), qos=1)
    except (requests.exceptions.RequestException, KeyError):
        logger.exception("Fetching events failed, retrying in %d seconds", sleep_time)
    time.sleep(sleep_time)
