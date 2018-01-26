import ds18x20
import machine
import network
import onewire
import time
import ujson
import urequests


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
        # The first 8 bits are a 1-Wire family code (DS18B20 code is 28h)
        # The next 48 bits are a unique serial number
        # The last 8 bits are a CRC of the first 56 bit
        # https://cdn.sparkfun.com/datasheets/Sensors/Temp/DS18B20.pdf

        # 0x8400000728e7b028        => 28-00000728e7b0
        # 0x8300000729d3be28        => 28-00000729d3be
        # CRC \  Serial  / Family

        sensor_uid = hex(int.from_bytes(sensor, 'little'))
        sensor_uid = "{}-{}".format(sensor_uid[-2:], sensor_uid[4:-2])
        sensor_temp = ds.read_temp(sensor)
        print('{}: {}'.format(sensor_uid, sensor_temp))

        send_influx(sensor_uid, sensor_temp, configs)

    print()


def send_influx(sensor_uid, sensor_temp, configs):
    # curl -i -XPOST "http://HOSTNAME:PORT/write?db=DBNAME&u=USERNAME&p=PASSWORD" --data-binary 'mymeas,mytag=1 myfield=91'

    # Build url
    url = 'http://{}:{}/write?db={}&u={}&p={}'.format(
        configs.get("influxdb").get("host"),
        configs.get("influxdb").get("port"),
        configs.get("influxdb").get("database"),
        configs.get("influxdb").get("username"),
        configs.get("influxdb").get("password")
    )
    print(url)

    # Create list of tags, first are sensor & machine uids
    tag_list = []
    tag_list.append("sensor={}".format(sensor_uid))

    # Machine UID
    machine_uid = machine.unique_id()
    esp_uid = hex(int.from_bytes(machine_uid, 'little'))
    tag_list.append("esp_uid={}".format(esp_uid))

    # Tags from config file
    tags = configs.get("tags")
    for key, value in tags.items():
        # escape commas and spaces
        value = value.replace(" ", "\ ")
        key = key.replace(" ", "\ ")
        value = value.replace(",", "\,")
        key = key.replace(",", "\,")

        # print('{}: {}'.format(key, value))
        tag_list.append('{}={}'.format(key, value))

    # Join tags from list to a string
    tag_string = ','.join(tag_list)
    data = '{},{} temp={}'.format(
        'temp',
        tag_string,
        sensor_temp
    )
    print(data)

    # data = "mymeas,mytag=1 myfield=91"
    r = urequests.post(url, data=data, headers={'Content-Type': 'application/octet-stream'})
    status_code = r.status_code
    if status_code is 204:
        print("Success")
    elif status_code is 400:
        print("Bad Request")
    elif status_code is 401:
        print("Unauthorized")
    elif status_code is 404:
        print("Not Found")
    elif status_code is 500:
        print("Internal Server Error")

    # It's mandatory to close response objects as soon as you finished
    # working with them. On MicroPython platforms without full-fledged
    # OS, not doing so may lead to resource leaks and malfunction.
    r.close()


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
