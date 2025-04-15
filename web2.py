from astropy.table import Table
import numpy as np
import pandas as pd

csv_file = 'MyEBirdData.csv'
# read as a Pandas DataFrame
tbl = pd.read_csv(csv_file)
# remove lines that do not have a value in 'ML Catalog Numbers'
tbl = tbl[tbl['ML Catalog Numbers'].notna()]
# loop through the DataFrame and duplicate lines that have
# multiple values in 'ML Catalog Numbers'
tbl['ML Catalog Numbers'] = tbl['ML Catalog Numbers'].str.split(' ')
tbl = tbl.explode('ML Catalog Numbers')
# sort Backwards by date
tbl['Date'] = pd.to_datetime(tbl['Date'])
# sort Backwards by date
tbl = tbl.sort_values(by='Date', ascending=False)

# rebase the index
tbl = tbl.reset_index(drop=True)



sizes = 480,1200,2400

id = np.array(tbl['ML Catalog Numbers'])[0]
url1200 = f'https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{id}/1200'



#tbl = tbl[tbl['Common Name'] == name]

id = tbl['ML Catalog Numbers'][0].split(' ')[0]

print(url1200.format(id))