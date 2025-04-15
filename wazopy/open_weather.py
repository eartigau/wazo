import numpy as np
from astropy.time import Time
from etienne_tools import save_pickle,read_pickle
import os
import matplotlib.pyplot as plt
import requests
from astropy.table import Table
import pyperclip

def upcase_first_letter(s):
    return s[0].upper() + s[1:]

def get_weather(latitude, longitude, dt, force=False):

    # we round to the closest 1000 seconds
    dt = int(np.round(dt,-3))

    # path where we store the weather data
    hidden_path = '/Users/eartigau/.openweathermap/'
    outname = '{}weather_data_lat{:.7f}_lon{:.7f}_dt{}.pkl'.format(hidden_path, latitude, longitude, int(dt))

    if not os.path.exists(outname) or force:
        API_key = 'cfb9653a9a3df3' + 'e1f6b7c9aed1fa55e7'
        url = f"https://api.opentopodata.org/v1/aster30m?locations={latitude},{longitude}"
        r = requests.get(url)
        data_altitude = r.json()
        url = "https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={}&lon={}&dt={}&appid={}&lang=fr"

        url = url.format(latitude, longitude, int(dt), API_key)
        weather_data = requests.get(url).json()

        if 'message' in weather_data.keys():
            raise ValueError('Error: {}'.format(weather_data['message']))


        weather_data['elevation'] = data_altitude['results'][0]['elevation']
        weather_data['timezone_offset_hours'] = weather_data['timezone_offset'] / 3600
        weather_data['elevation dataset'] = data_altitude['results'][0]['dataset']
        tz = weather_data['timezone_offset']


        for ite in range(2):
            weather_data2 = dict(weather_data)
            for key in weather_data2.keys():
                if type(weather_data[key]) == list:
                    for key2 in weather_data[key][0].keys():
                        if type(weather_data[key][0][key2]) == dict:
                            for key3 in weather_data[key][0][key2].keys():
                                weather_data['{}_{}_{}'.format(key, key2, key3)] = weather_data[key][0][key2][key3]
                        else:
                            weather_data['{}_{}'.format(key, key2)] = weather_data[key][0][key2]
                    del weather_data[key]


        sunrise = 'h'.join(
            Time(weather_data['data_sunrise'] + tz, format='unix').iso.split(' ')[1].split(':')[0:2])
        sunset = 'h'.join(
            Time(weather_data['data_sunset'] + tz, format='unix').iso.split(' ')[1].split(':')[0:2])

        data_wind_dir = weather_data['data_wind_deg']
        # in direction
        if data_wind_dir < 0:
            data_wind_dir[data_wind_dir < 0] += 360
        if data_wind_dir > 360:
            data_wind_dir[data_wind_dir > 360] -= 360
        weather_data['data_wind_dir'] = data_wind_dir
        # expressed in N, E, S, W with 45 deg resolution
        wind_en = np.array(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'])
        wind_en = wind_en[int(np.round(data_wind_dir / 45))]
        wind_fr = np.array(['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO', 'N'])
        wind_fr = wind_fr[int(np.round(data_wind_dir / 45))]

        weather_data['data_wind_dir_en'] = wind_en
        weather_data['data_wind_dir_fr'] = wind_fr

        weather_data['sunrise-hour'] = sunrise
        weather_data['sunset-hour'] = sunset
        weather_data['TIME-ISO-LOCAL'] = Time(weather_data['data_dt'] + tz, format='unix').iso.split('.0')[0]
        weather_data['TIME-ISO-UTC'] = Time(weather_data['data_dt'] , format='unix').iso.split('.0')[0]
        weather_data['DATE-ISO-LOCAL'] = Time(weather_data['data_dt'] , format='unix').iso.split(' ')[0]
        weather_data['DATE-ISO-UTC'] = Time(weather_data['data_dt'] + tz, format='unix').iso.split(' ')[0]
        weather_data['TIMEofDAY'] = Time(weather_data['data_dt'] + tz, format='unix').iso.split(' ')[1].split('.0')[0]
        weather_data['TIMEofDAY-UTC'] = Time(weather_data['data_dt'] , format='unix').iso.split(' ')[1].split('.0')[0]

        weather_dico = {}
        weather_dico['01d'] = '☀️'
        weather_dico['01n'] = '🌙'
        weather_dico['02d'] = '⛅'
        weather_dico['02n'] = '⛅'
        weather_dico['03d'] = '☁️'
        weather_dico['03n'] = '☁️'
        weather_dico['04d'] = '☁️'
        weather_dico['04n'] = '☁️'
        weather_dico['09d'] = '🌧️'
        weather_dico['09n'] = '🌧️'
        weather_dico['10d'] = '🌦️'
        weather_dico['10n'] = '🌦️'
        weather_dico['11d'] = '⛈️'
        weather_dico['11n'] = '⛈️'
        weather_dico['13d'] = '🌨️'
        weather_dico['13n'] = '🌨️'
        weather_dico['50d'] = '🌫️'
        weather_dico['50n'] = '🌫️'

        if weather_data['data_weather_icon'] in weather_dico.keys():
            weather_data['data_weather_icon2'] = weather_dico[weather_data['data_weather_icon']]
        else:
            stop

        weather_data['data_weather_description'] = upcase_first_letter(weather_data['data_weather_description'])

        txt = weather_data['data_weather_description']+'\t'+weather_data['data_weather_icon2']+\
                '\nTempérature : {:.0f}°C\n'.format(np.round(weather_data['data_temp']-273.15))+\
                'Humidité : {:.0f}%\n'.format(weather_data['data_humidity'])+\
                'Vent : {:.0f} km/h ({})\n'.format(weather_data['data_wind_speed'],weather_data['data_wind_dir_fr'])+\
                'Lever du soleil : {}\n'.format(weather_data['sunrise-hour'])+\
                'Coucher du soleil : {}\n'.format(weather_data['sunset-hour'])+\
                'Altitude : {:.0f} m\n'.format(weather_data['elevation'])

        weather_data['full_description'] = txt
        save_pickle(outname, weather_data)
    else:
        #print('Reading from pickle file : {}'.format(outname))
        weather_data = read_pickle(outname)

    return weather_data

latitude = 45.48557775240364
longitude = -73.62931226944201


tbl = Table.read('/Users/eartigau/oiseaux3/ebird/MyEBirdData.csv')
# only keep the checklist with comments
tbl = tbl[np.unique(tbl['Submission ID'],return_index=True)[1]]
tbl = tbl[['Altitude : ' not in cmt for cmt in tbl['Checklist Comments']]]
tbl = tbl[[':' in tt for tt in tbl['Time']]]

# randomize the order
#np.random.seed(0)
idx = np.random.permutation(len(tbl))
tbl = tbl[idx]

#tbl = tbl[500::-1]

latitudes = np.array(tbl['Latitude'])
longitudes = np.array(tbl['Longitude'])
date = np.array(tbl['Date'])
time = np.array(tbl['Time'])

data_weather_icon = []
actual_icon = []
elevation = []

for i in range(len(tbl)):
    t1,t2 = time[i].split(':')
    t2 = t2.split(' ')[0]
    if 'PM' in time[i]:
        if t1 !='12': # 12 PM is noon
         t1 = str(int(t1)+12)

    yr, mo, day = date[i].split('-')
    hh, mm = t1, t2
    latitude = latitudes[i]
    longitude = longitudes[i]

    dt = Time('{}-{}-{}T{}:{}:00'.format(yr, str(mo).zfill(2), str(day).zfill(2),
                                         str(hh).zfill(2), str(mm).zfill(2))).unix

    force = False

    try:
        weather_data = get_weather(latitude, longitude, dt, force=force)
        tz = weather_data['timezone_offset']
        weather_data = get_weather(latitude, longitude, dt - tz, force=force)
    except:
        print('error')
        continue

    data_weather_icon.append(weather_data['data_weather_icon'])
    actual_icon.append(tbl['Checklist Comments'][i])
    print('\n\n\n\n')
    #print(tbl[i])
    print('\t'+tbl[i]['Date'])

    keys = np.array( [key for key in weather_data.keys()])
    for ii in range(len(keys)):
        print(keys[ii],weather_data[keys[ii]])
    # set in pyperclip the weather data
    pyperclip.copy(weather_data['full_description'])
    #https://ebird.org/edit/effort?subID=S112845585
    cmd = 'open https://ebird.org/checklist/\?subID\={}'.format(tbl['Submission ID'][i])
    # new url : https://ebird.org/edit/effort?subID=S127672004

    #cmd = 'open https://ebird.org/edit/effort/\?subID={}'.format(tbl['Submission ID'][i])
    os.system(cmd)
    input('Press enter to continue')
    elevation.append(weather_data['elevation'])
    #stop