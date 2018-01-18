import ds18x20
import machine
import onewire
import time
import ujson

print('Welcome to uESP-logger')
print('======================')
print()

# Read config
f = open('config.json', 'r')
configs = ujson.loads(f.read())
f.close()

# InfluxDB configs
influx_host = configs.get("influxdb").get("host")
influx_port = configs.get("influxdb").get("port")
influx_database = configs.get("influxdb").get("database")
influx_username = configs.get("influxdb").get("username")
influx_password = configs.get("influxdb").get("password")

# Tags
print('Tags')
tags = configs.get("tags")
for key, value in tags.items():
    print('{}: {}'.format(key, value))

# TODO add sensor id & machine id as tags
# machine.unique_id()

print()

# the device is on GPIO12
dat = machine.Pin(12)

# create the onewire object
ds = ds18x20.DS18X20(onewire.OneWire(dat))

# scan for devices on the bus
sensors = ds.scan()
sensors_num = len(sensors)
print('Found {} devices.'.format(sensors_num))


# Get data from sensors
print('Temperatures:')
ds.convert_temp()
time.sleep_ms(1000)
for sensor in sensors:
    # https://forum.micropython.org/viewtopic.php?t=3677
    # TODO: is this correct format for serial number?
    sensor_uid = hex(int.from_bytes(sensor, 'little'))
    sensor_temp = ds.read_temp(sensor)
    print('{}: {}'.format(sensor_uid, sensor_temp))

print()

print(machine.unique_id())

# # TODO # #
# Make main loop
#   Sleep configured amount between meansurements
# Configure ESP
#   Deep sleep between meansurements
# Configurations
#   PIN?
#   Network settings
#   Sleep interval & type
# Send data to Influx
#   Build data string
#   Send to REST api
# Network
#   Reconnect wlan if disconnected
#   Configurable network settings
# Startup
#   Install everything necessary on startup (upip stuff)
#   Configure network
