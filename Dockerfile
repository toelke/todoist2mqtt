FROM python:3.13.3

RUN pip install --no-cache-dir paho-mqtt requests

WORKDIR /app
COPY *.py /app

#ENV MQTT_BROKER
#ENV MQTT_TOPIC
#ENV TODOIST_API_KEY

CMD ["python3", "/app/todoist2mqtt.py"]
