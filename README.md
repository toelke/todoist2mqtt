# todoist2mqtt
A program to publish the activity log of your todoist account to MQTT.

To run:

```
docker run -d --restart=unless-stopped --name todoist2mqtt -e TODOIST_API_KEY=123456789 toelke158/todoist2mqtt:latest
```

Get the todoist API key from https://todoist.com/prefs/integrations (at the very bottom).

Events will look like described [here](https://developer.todoist.com/sync/v8/#activity).

## Customization

Apart from using the environment variable `TODOIST_API_KEY` to set your API key, you can use the following environment variables:

* `MQTT_BROKER` to set the MQTT broker (default is 127.0.0.1)
* `MQTT_TOPIC` to set the MQTT topic (default is "todoist/activity")
