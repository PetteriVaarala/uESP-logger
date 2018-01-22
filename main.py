import ds18x20
import machine
import network
import onewire
import time
import ujson


def main():

    print('Welcome to uESP-logger')
    print('======================')
    print()

    # Read config
    f = open('config.json', 'r')
    configs = ujson.loads(f.read())
    f.close()

    # Check network
    network_setup(configs)

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
    esp_pin = configs.get("esp").get("1wire_pin")
    dat = machine.Pin(esp_pin)

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


def network_setup(configs):
    print("Checking network..")

    nic = network.WLAN(network.STA_IF)

    # If not connected
    while not nic.isconnected():
        print("Activing..")
        nic.active(True)
        time.sleep(5)

        ssid = configs.get("network").get("ssid")
        password = configs.get("network").get("password")

        # Scan for available access points
        # print("Scanning..")
        # available_ssids = nic.scan()
        # if ssid not in dict(available_ssids):
        #    print("SSID {} not found.".format(ssid))
        #    print("Available SSIDs {}:".format(available_ssids))

        # Connect to an AP
        print('Connecting.. {} / {}'.format(ssid, password))
        nic.connect(ssid, password)
        time.sleep(5)

        if not nic.isconnected():
            print("Not connected, sleeping 30s and trying again..")
            time.sleep(30)

    print("Connected.")


if __name__ == "__main__":
    main()


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
