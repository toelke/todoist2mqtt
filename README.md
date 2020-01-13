# todoist2mqtt
A program to publish the activity log of your todoist account to MQTT.

To run:

```
docker run --name todoist2mqtt -e MQTT_BROKER=127.0.0.1 -e MQTT_TOPIC=todoist/activity -e TODOIST_API_KEY=123456789
```

Get the todoist API key from todoist.com/prefs/integrations (at the very bottom).

Events will look like described [here](https://developer.todoist.com/sync/v8/#activity).
