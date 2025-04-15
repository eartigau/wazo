import numpy as np
from astropy.table import Table
import pandas as pd
from PIL.ExifTags import TAGS
import glob
import datetime
from astropy.time import Time
from PIL import Image
import dateutil.parser
from datetime import datetime 
from etienne import *






all_lists = pd.read_csv('toto.csv')
all_ids = all_lists['Submission ID']
all_ids = np.array(all_ids)
#all_ids.sort()
#
#keep = np.zeros(len(all_ids))
#for i in range(len(all_ids)-1):
#	keep[i] = (all_ids[i]!=all_ids[i+1])
#
#all_ids = all_ids[keep ==1]

for list_id in all_ids:
	outname = 'ebird_lists/'+list_id

	if os.path.isfile(outname) == False:
		url = 'https://ebird.org/canada/view/checklist/'+list_id

		os.system("wget --no-check-certificate "+url)
		os.system("mv "+list_id+' '+outname)
		os.system('grep '+"This checklist has been flagged"+' '+outname)
	else:
		print(outname +' existe')
 		#"This checklist has been flagged"


