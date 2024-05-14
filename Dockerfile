FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY healthcheck.sh .
RUN chmod +x healthcheck.sh

# Setting the environment variables  (optional, could also be done via docker-compose.yml)
ENV MQTT_SERVER=192.168.178.74
ENV MQTT_PORT=1883
ENV MQTT_TOPIC=/lora/
ENV TEMPERATURE_TOPIC=bridge/temperature
ENV UPTIME_TOPIC=bridge/uptime
ENV SERIAL_URL=/dev/ttyS0
ENV SERIAL_BAUDRATE=9600
ENV SLEEP_INTERVAL=60

# Healthcheck-Configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD ./healthcheck.sh

CMD ["python", "main.py"]
