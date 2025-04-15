from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource, GMapOptions
from bokeh.plotting import gmap
from astropy.table import Table
import numpy as np
from bokeh.plotting import figure, show, output_file
from bokeh.tile_providers import get_provider, Vendors
from pyproj import Proj, transform 


tbl = Table.read('ebird/MyEBirdData.csv')


xx,yy = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), tbl['LONGITUDE'],tbl['LATITUDE'])

#source = ColumnDataSource(
#    data=dict(lat=np.array(tbl['Latitude']),
#              lon=np.array(tbl['Longitude']))
#)


source = ColumnDataSource(
    data=dict(xx=xx,
              yy=yy)
)



output_file("tile.html")

tile_provider = get_provider(Vendors.CARTODBPOSITRON)

# range bounds supplied in web mercator coordinates
p = figure(
           x_axis_type="mercator", y_axis_type="mercator")
p = figure()

p.add_tile(tile_provider)

p.circle(x="xx", y="yy", size=8, fill_color="red", fill_alpha=0.5, source=source)

show(p)

stop
exit
