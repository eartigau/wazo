from astropy.table import Table
import matplotlib.pyplot as plt
import numpy as np
import geopandas

tbl = Table.read('MyEBirdData.csv')

tbl = tbl[tbl['COMMON_NAME']=='Mésange à tête noire']

lat = tbl['LATITUDE']
lon =  tbl['LONGITUDE']

uloc = np.unique(tbl['LOCATION'])

world.plot()
world.boundary.plot();
for i in range(len(uloc)):
    g = tbl['LOCATION'] == uloc[i]
    n = np.sum(g)

    lat0=lat[g][0]
    lon0=lon[g][0]
    rr= 4*(n)**0.25
    plt.plot(lon0,lat0,markersize = rr,marker = 'o',zorder = 1.0/n,color='red',alpha=.3)
plt.show()