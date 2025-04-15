#from astropy.table import Column
#from PIL.ExifTags import TAGS
#from astropy.io import ascii
from oiseaux.drag import *

tbl_fr = Table.read('sensible_fr.csv')
tbl_taxo = Table.read('ebird/eBird_Taxonomy_v2019.csv')
tbl_taxo['FR'] = np.zeros_like(tbl_taxo,dtype = 'U99')
tbl_taxo['SENSIBLE'] = np.zeros_like(tbl_taxo,dtype = bool)


for i in range(len(tbl_taxo)):
     g = tbl_taxo['SPECIES_CODE'][i] == tbl_fr['ID']
     
     if np.sum(g) == 1:
         tbl_taxo['FR'][i] = np.array(tbl_fr['FR'][g])[0] 
         tbl_taxo['SENSIBLE'][i] = np.array(tbl_fr['sensible'][g])[0] == 'True'
         print(tbl_fr['FR'][g], np.array(tbl_fr['sensible'][g])[0])
     else:
         g = tbl_taxo['REPORT_AS'][i] == tbl_fr['ID']
         if np.sum(g) == 1:
             tbl_taxo['FR'][i] = np.array(tbl_fr['FR'][g])[0]
             tbl_taxo['SENSIBLE'][i] = np.array(tbl_fr['sensible'][g])[0] == 'True'
             print(tbl_fr['FR'][g], np.array(tbl_fr['sensible'][g])[0])
         