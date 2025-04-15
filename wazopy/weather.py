# Import Meteostat library and dependencies
from datetime import datetime
import matplotlib.pyplot as plt
from meteostat import Point, Daily, Hourly
import numpy as np
from wazo import get_ebird

ebird = get_ebird()


lat = float(ebird['LATITUDE'][0])
lon = float(ebird['LONGITUDE'][0])

location = Point(lat, lon)

"""
Column	Description	Type
station	The Meteostat ID of the weather station (only if query refers to multiple stations)	String
time	The datetime of the observation	Datetime64
temp	The air temperature in °C	Float64
dwpt	The dew point in °C	Float64
rhum	The relative humidity in percent (%)	Float64
prcp	The one hour precipitation total in mm	Float64
snow	The snow depth in mm	Float64
wdir	The average wind direction in degrees (°)	Float64
wspd	The average wind speed in km/h	Float64
wpgt	The peak wind gust in km/h	Float64
pres	The average sea-level air pressure in hPa	Float64
tsun	The one hour sunshine total in minutes (m)	Float64
coco	The weather condition code	Float64
"""
# Set time period
start = datetime(2022, 1, 10, 12, 00)
end = datetime(2022, 1, 10, 16, 59)

# Get hourly data
data = Hourly(location, start, end)
data = data.fetch()

temp =  np.array(data.temp)
t12 = np.round(np.min(temp),1),np.round(np.max(temp),1)
print('Temperature : {} <> {} C'.format(t12[0],t12[1]))
print('Vent : {} km/s'.format(np.round(np.mean(data.wspd))))
# Print DataFrame
print(data)