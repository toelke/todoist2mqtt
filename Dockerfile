FROM python:3

RUN pip install paho-mqtt todoist-python

WORKDIR /app
ADD *.py /app

ENV MQTT_BROKER
ENV MQTT_TOPIC
ENV TODOIST_API_KEY

CMD python3 todoist2mqtt.py
