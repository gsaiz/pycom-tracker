# pycom-tracker

IoT tracker device built with a Pycom FiPy.

## Features

- Scan nearby WiFi APs (WLAN scans) to get locations using [Google Geolocation API](https://developers.google.com/maps/documentation/geolocation/overview).

- Send WLAN scans over LoRaWAN.

- Acquire location using a UART GPS module (u-blox M6/M7/M8).

- Log WLAN scans and GPS locations to SD card.

- Convert WLAN scans to coordinates and plot them in Google Maps.


## How to configure the IoT device

1. Edit the [config.json](./upython/configs/config.json) file to enable/disable features.
2. Rename the []() file to []() with the required credentials.
3. Using Pycom's VS Code extension [Pymakr](https://marketplace.visualstudio.com/items?itemName=pycom.Pymakr), click upload to save all the files to the pycom's flash memory.

## How to plot the device's locations in Google Maps

If the device has the datalogger feature on (*SAVE_TO_SD* set to *true* in [config.json](./upython/configs/config.json)), then you can plot the device's location history on Google Maps.

1. Copy the contents of the SD card to the [sd](./sd) folder.
2. To convert WLAN scans to GPS coordinates using Google Geolocation API, run the [google_maps_plots/convert_scans_to_locations.py](./google_maps_plots/convert_scans_to_locations.py) script. 
3. To plot the WLAN scans & GPS coordinates on Google Maps, run the [google_maps_plots/plot_coordinates.py](./google_maps_plots/plot_coordinates.py) script.
