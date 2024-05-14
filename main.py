import asyncio
import serial_asyncio
import logging
import os
import paho.mqtt.client as mqtt
import time
from datetime import datetime

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
handler = logging.FileHandler('/app/healthcheck.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Environment variables for MQTT
MQTT_SERVER = os.getenv('MQTT_SERVER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'lora/')
TEMPERATURE_TOPIC = os.getenv('TEMPERATURE_TOPIC', 'bridge/temperature')
UPTIME_TOPIC = os.getenv('UPTIME_TOPIC', 'bridge/uptime')
SLEEP_INTERVAL = os.getenv('SLEEP_INTERVAL', 60)
# Environment variables for Serial
SERIAL_URL = os.getenv('SERIAL_URL', '/dev/ttyS0')
SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', 9600))

# MQTT client setup
mqtt_client = mqtt.Client()

# Function to read Raspberry Pi temperature
def get_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read()
        temp_c = float(temp_str) / 1000.0
        return temp_c
    except Exception as e:
        logging.error(f"Error reading temperature: {str(e)}")
        return None

# Function to get container uptime
def get_uptime():
    try:
        stat = os.stat('/proc/1')
        start_time = datetime.fromtimestamp(stat.st_ctime)
        uptime = datetime.now() - start_time
        return str(uptime).split('.')[0]  # Return uptime as HH:MM:SS
    except Exception as e:
        logging.error(f"Error reading uptime: {str(e)}")
        return None

# Function to periodically publish temperature and uptime
async def publish_system_info():
    while True:
        temp = get_temperature()
        if temp is not None:
            mqtt_client.publish(TEMPERATURE_TOPIC, f"Temperature: {temp} °C")
            logging.info(f"Temperature published to {TEMPERATURE_TOPIC}: {temp} °C")

        uptime = get_uptime()
        if uptime is not None:
            mqtt_client.publish(UPTIME_TOPIC, f"Uptime: {uptime}")
            logging.info(f"Uptime published to {UPTIME_TOPIC}: {uptime}")

        await asyncio.sleep(SLEEP_INTERVAL)  # Wait for 60 seconds before the next publish

async def read_serial(loop):
    try:
        # Attempt to open the serial connection
        reader, _ = await serial_asyncio.open_serial_connection(url=SERIAL_URL, baudrate=SERIAL_BAUDRATE)
        logging.info("Serial connection opened.")

        # Log a health check message for Serial
        logging.info("HEALTHCHECK: Serial connection successfully established.")

        while True:
            try:
                # Read data until a newline character is found
                data = await reader.readuntil(b'\n')
                # Decode the data
                message = data.decode().strip()
                logging.info(f"Received message: {message}")

                # Publish the message to the MQTT server
                mqtt_client.publish(MQTT_TOPIC, message)
                logging.info(f"Message published to {MQTT_TOPIC}")
            except asyncio.IncompleteReadError:
                logging.error("Incomplete read from serial port, possible data corruption or connection issue.")
            except UnicodeDecodeError:
                logging.error("Error decoding message, data might be corrupted.")
            except Exception as e:
                logging.error(f"An unexpected error occurred while reading from the serial port: {str(e)}")
                break  # Exit the loop on unexpected errors

    except serial_asyncio.serial.SerialException as e:
        logging.critical(f"Serial connection could not be established: {str(e)}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred during setup: {str(e)}")

async def main():
    loop = asyncio.get_event_loop()
    try:
        # Connect to MQTT server
        mqtt_client.connect(MQTT_SERVER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        # Log a health check message for MQTT Connection
        logging.info("HEALTHCHECK: MQTT connection successfully established.")

        # Start tasks
        await asyncio.gather(
            read_serial(loop),
            publish_system_info()
        )
    except KeyboardInterrupt:
        logging.info("Program terminated by user.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred in the main loop: {str(e)}")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        loop.close()
        logging.info("Event loop closed.")

if __name__ == "__main__":
    asyncio.run(main())
