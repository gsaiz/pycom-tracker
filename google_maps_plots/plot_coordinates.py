import os
import json
import math

import gmplot
from dotenv import load_dotenv

load_dotenv('../.env')  # take environment variables from .env.

MAP_CENTRAL_LATITUDE = os.getenv('MAP_CENTRAL_LATITUDE')
MAP_CENTRAL_LONGITUDE = os.getenv('MAP_CENTRAL_LONGITUDE')
GOOGLE_API_KEY = os.getenv("GOOGLE_GEOLOCATION_API_KEY")

COLORS = {
    'GREEN': '#00FF00',
    'BLUE': '#0000FF',
}


def dms2dd(location_dms):
    """Convert GPS coodinates from Degrees, Minute and Seconds (DMS) to Decimal Degrees (DD) format."""
    location_dd = {}
    for coord, value in location_dms.items():
        degree, seconds, minutes = value[0], *math.modf(value[1])
        location_dd[coord] = degree + minutes / 60 + seconds / 3600
    
    return location_dd


gmap = gmplot.GoogleMapPlotter(MAP_CENTRAL_LATITUDE, MAP_CENTRAL_LONGITUDE, 14, apikey=GOOGLE_API_KEY)

# Plot WLAN scans
path_wlan_scans = './locations/wlan_scans_locations.txt'
try:
    with open(path_wlan_scans) as fin:
        coordinates = [json.loads(line) for line in fin]
except FileNotFoundError:
    print(f'WLAN scans locations not found in {path_wlan_scans}')
else:
    gmap.scatter([loc['location']['lat']for loc in coordinates], [loc['location']['lng']for loc in coordinates], color=COLORS['GREEN'], size=[loc['accuracy'] for loc in coordinates], marker=False)

# Plot GPS coordinates
path_gps_locations = '../sd/gps_locations.txt'
try:
    with open(path_gps_locations) as fin:
        coordinates = [json.loads(line) for line in fin]
except FileNotFoundError:
    print(f'GPS locations not found in {path_wlan_scans}')
else:
    # Convert from DMS to DD
    coordinates_dd = [dms2dd(loc) for loc in coordinates]
    # GPS accuracy is unknown
    gmap.scatter([loc['latitude'] for loc in coordinates_dd], [loc['longitude']for loc in coordinates_dd], color=COLORS['BLUE'], size=30, marker=False)


gmap.draw('map.html')
# Open the map with the default system's browser
os.startfile('map.html')
