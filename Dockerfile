FROM python:3.11.5

RUN pip install --no-cache-dir paho-mqtt requests

WORKDIR /app
COPY *.py /app

#ENV MQTT_BROKER
#ENV MQTT_TOPIC
#ENV TODOIST_API_KEY

CMD ["python3", "/app/todoist2mqtt.py"]
