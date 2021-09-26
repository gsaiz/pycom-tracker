import json
import os
import datetime

import requests
from dotenv import load_dotenv

load_dotenv('../.env')  # take environment variables from .env.

GOOGLE_GEOLOCATION_API_KEY = os.getenv('GOOGLE_GEOLOCATION_API_KEY')

with open('../sd/wlan_scans.txt') as fin:
    wlan_scans = [json.loads(line) for line in fin]

print(f'Found {len(wlan_scans)} wlan scans')
file_out_path = './locations/wlan_scans_locations.txt'
if os.path.exists(file_out_path):
    inp = input(f'File {file_out_path} exists and will be overwritten, continue? [Y/N]\n')
    if inp.lower() != 'y':
        print('Exiting...')
        raise SystemExit

unknown_locations_count = 0
with open(file_out_path, 'w') as fout:
    for num, wlan_scan in enumerate(wlan_scans, start=1):
        print(f'Querying Google Geolocation API {num}/{len(wlan_scans)}')
        google_api_body = {
            'considerIp': False,
            'wifiAccessPoints': wlan_scan,
        }
        response = requests.post(
            url=f'https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_GEOLOCATION_API_KEY}',
            json=google_api_body,
        )
        # Handle Google Geolocation API properly
        if response.status_code == 404:
            # Reason 	Domain 	        HTTP Status Code 	Description
            # notFound 	geolocation 	404 	            The request was valid, but no results were returned.
            unknown_locations_count+= 1
            print('Found an unknown location')
        else:
            response.raise_for_status()
            location = response.json()
            fout.write(f'{json.dumps(location)}\n')
