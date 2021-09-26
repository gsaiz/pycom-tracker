import ubinascii
import ujson
import time
import os
import socket
import time

import pycom
from network import WLAN, LoRa
from machine import SD, deepsleep, UART

from libs import urequests
import libpayload
from libs.micropyGPS import MicropyGPS


def scan_wlans():
    # Init WiFi
    wlan = WLAN()
    wlan.init(mode=WLAN.STA)

    # Scan for WiFi networks
    nets = wlan.scan()

    # Print results
    for net in nets:
        print('Found WiFi network: {}'.format(net))
    
    # Deinit WiFi
    wlan.deinit()

    # Format for Google Geolocation API
    nets_formatted = []
    for net in nets:
        mac_hex = ubinascii.hexlify(net.bssid).decode('utf8')
        nets_formatted.append(
            {
                'macAddress': ':'.join([mac_hex[i:i+2] for i in range(0, len(mac_hex), 2)]),
                'signalStrength': net.rssi,
                'signalToNoiseRatio': 0,
                'channel': net.channel,
                'age': 0,
            }
        )

    return nets_formatted


def get_location_google_api(nets_formatted, creds):
    
    google_api_body = {
        'considerIp': False,
        'wifiAccessPoints': nets_formatted,
    }
    print('Google Geolocation API body:\n{}'.format(ujson.dumps(google_api_body)))

    # Connect to WiFi
    print('Connecting to WiFi')
    wlan = WLAN(mode=WLAN.STA)
    wlan.connect(ssid=creds['WLAN_SSID'], auth=(WLAN.WPA2, creds['WLAN_WPA2_PASSWORD']))
    connect_timeout = 10  # s
    time_start = time.time()
    while not wlan.isconnected():
        if time.time() - time_start > connect_timeout:
            print('WiFi connect timeout at {} s'.format(connect_timeout))
            return None

    print('WiFi connected!')
    time.sleep(1)

    # Request to Google Geolocation API
    response = urequests.post(
        url='https://www.googleapis.com/geolocation/v1/geolocate?key={}'.format(creds['GOOGLE_GEOLOCATION_API_KEY']),
        json=google_api_body,
    )
    location = response.json()
    print('Google Geolocation API response: {}'.format(location))

    url_maps = 'https://www.google.com/maps/search/?api=1&query={lat}%2C{lng}'.format(
        lat=location['location']['lat'],
        lng=location['location']['lng'],
    )
    print('Google Maps URL: {}'.format(url_maps))

    # Deinit WiFi
    wlan.deinit()

    return location


def save_to_sd(wlan_nets, google_api_location, gps_location):
    # Save results to SD card
    sd = SD()
    sd.init()
    os.mount(sd, '/sd')

    if wlan_nets:
        print('Saving wlan scans to SD card...')
        with open('/sd/wlan_scans.txt', 'a') as fout:
            nets_formatted_str = ujson.dumps(wlan_nets)
            fout.write('{}\n'.format(nets_formatted_str))

    if google_api_location:
        print('Saving Google API location to SD card...')
        with open('/sd/google_api_locations.txt', 'a') as fout:
            location_str = ujson.dumps(google_api_location)
            fout.write('{}\n'.format(location_str))

    if gps_location:
        print('Saving GPS location to SD card...')
        with open('/sd/gps_locations.txt', 'a') as fout:
            location_str = ujson.dumps(gps_location)
            fout.write('{}\n'.format(location_str))

    os.umount('/sd')
    sd.deinit()


def send_lora(wlan_nets, creds):
    print('LoRaWAN start')

    # Initialise LoRa in LORAWAN mode.
    # Please pick the region that matches where you are using the device:
    # Asia = LoRa.AS923
    # Australia = LoRa.AU915
    # Europe = LoRa.EU868
    # United States = LoRa.US915
    lora = LoRa(
        mode=LoRa.LORAWAN, region=LoRa.EU868, adr=True, public=True, device_class=LoRa.CLASS_A, tx_retries=2, sf=7)

    # create an OTAA authentication parameters, change them to the provided credentials
    app_eui = ubinascii.unhexlify(creds['LORAWAN_APP_EUI'])
    app_key = ubinascii.unhexlify(creds['LORAWAN_APP_KEY'])

    # Uncomment for US915 / AU915 & Pygate
    # for i in range(0,8):
    #     lora.remove_channel(i)
    # for i in range(16,65):
    #     lora.remove_channel(i)
    # for i in range(66,72):
    #     lora.remove_channel(i)

    print('LoRaWAN restoring state from nvram...')
    lora.nvram_restore()

    if not lora.has_joined():
        # join a network using OTAA (Over the Air Activation)
        # SF9 --> DR3 (EU868)
        lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0, dr=3)

        # wait until the module has joined the network
        while not lora.has_joined():
            print('Not yet joined...')
            time.sleep(2.5)

    print('LoRaWAN joined')
    print('LoRaWAN saving state to nvram...')
    lora.nvram_save()
    # create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    # set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 2)

    # make the socket blocking
    # (waits for the data to be sent and for the 2 receive windows to expire)
    s.setblocking(True)

    # send some data
    # Pack data to send
    data = libpayload.pack(wlan_nets, max_n=5)
    print('LoRaWAN sending ({} Bytes): {}'.format(len(data), ubinascii.hexlify(data)))
    s.send(data)

    # make the socket non-blocking
    # (because if there's no data received it will block forever...)
    s.setblocking(False)

    # get any data received (if any...)
    data_received = s.recv(64)
    s.close()
    print('LoRaWAN received ({} Bytes): {}'.format(len(data_received), data_received))

    print('LoRaWAN end')


def load_json(path):
    contents = {}
    try:
        with open(path, 'r') as fin:
            contents = ujson.loads(fin.read())
            # Don't read keys that start with "_"
            contents = {key: value for key, value in contents.items() if not key.startswith('_')}
    except FileNotFoundError:
        pass

    return contents


def get_gps_location():
    print('Setting up UART port for GPS...')
    # Setup UART
    uart = UART(1)
    uart.init(baudrate=9600, pins=('P22', 'P23'), bits=8, parity=None, stop=1, rx_buffer_size=4096)
    time.sleep(1.5)

    # Setup MicropyGPS
    gps = MicropyGPS()

    timeout = 20  # s
    time_start = time.time()
    location = {}
    while True:
        if time.time() - time_start > timeout:
            print('GPS location read timeout')
            break
        if uart.any():
            stat = gps.update(uart.read(1).decode('ascii'))
            if stat:
                location = {
                    'latitude': gps.latitude,
                    'longitude': gps.longitude,
                }
                print('GPS location: {}'.format(location))
                break

    return location


# Disable LED heartbeat
pycom.heartbeat(False)

COLORS = {
    'RED': 0xFF0000,
    'GREEN': 0x00FF00,
    'BLUE': 0x0000FF,
}

# Load config
config = load_json('configs/config.json')

# Load credentials
creds = load_json('configs/creds.json')

# Scan WLAN networks
wlan_nets = []
try:
    wlan_nets = scan_wlans()
except Exception as ex:
    print('Exception scanning WLAN networks: {}'.format(ex))
else:
    # Turn LED green on successful wlan scan
    pycom.rgbled(COLORS['GREEN'])

# Get current device location using Google Geolocation API
google_api_location = None
if config['GOOGLE_GEOLOCATION_API']:
    try:
        google_api_location = get_location_google_api(wlan_nets, creds)
    except Exception as ex:
        print('Exception getting Google API location: {}'.format(ex))

# Read position from GPS
gps_location = None
if config['GPS']:
    try:
        gps_location = get_gps_location()
    except Exception as ex:
        print('Exception getting GPS location: {}'.format(ex))

# Save results to SD
if config['SAVE_TO_SD']:
    try:
        save_to_sd(wlan_nets, google_api_location, gps_location)
    except Exception as ex:
        print('Exception saving to SD: {}'.format(ex))
    else:
        # Turn LED blue on successful SD save
        pycom.rgbled(COLORS['BLUE'])
        time.sleep(1)


# Send WLAN scan via LoRaWAN
if config['LORAWAN']:
    try:
        send_lora(wlan_nets, creds)
    except Exception as ex:
        print('Exception sending via LoRaWAN: {}'.format(ex))

# Go to sleep until next cycle
print('Going to sleep for {} s'.format(config['CYCLE_SLEEP_S']))
deepsleep(config['CYCLE_SLEEP_S'] * 1000)
